---
name: 323-pytorch
description: >
  Comprehensive best practices for writing production-quality PyTorch code. Use this skill
  whenever the user is writing, reviewing, debugging, or optimizing PyTorch code — including
  model definitions, training loops, data pipelines, GPU/CPU transfers, memory management,
  and inference. Trigger for any task involving neural networks, deep learning, tensors,
  dataloaders, loss functions, optimizers, or model deployment in PyTorch. Also trigger
  when the user asks about common PyTorch pitfalls, performance issues, or wants to convert
  PyTorch code from "it works" to production-ready.
tags:
  - python
  - pytorch
  - deep-learning
  - neural-networks
  - cuda
  - amp
  - performance
capabilities:
  actions:
    - optimize_training_loops
    - validate_model_arch
    - configure_high_throughput_datasets
    - implement_mixed_precision
    - profile_tensor_shapes
  file_extensions:
    - .py
    - .pt
    - .pth
    - .yaml
    - .json
triggers:
  verbs:
    - train
    - optimize
    - refactor
    - validate
    - profile
    - compile
  nouns:
    - PyTorch
    - nn.Module
    - DataLoader
    - Tensor
    - CUDA
    - AMP
    - SGD
    - AdamW
manifest:
  knowledge_base:
    - assets/torch_metadata.json
    - assets/manifest.json
  logic_examples:
    - examples/training_pipeline.py
---

# PyTorch High-Performance & Best Practices (Skill 323)

This skill enforces mandatory architecture and best practices for writing production-quality PyTorch code. It details patterns for robust, enterprise-grade workflows using **Mixed Precision (AMP)**, **Kernel Fusion (torch.compile)**, **Asynchronous Data Transfer**, and clean separation of concerns.

---

## 1. Tensor & Device Management

**Always be explicit about device placement.**
```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
x = x.to(device)           # move inputs; do NOT rely on implicit casting
```

**Avoid `.cuda()` hardcoding** — use `.to(device)` so code runs on CPU, MPS (Apple Silicon), or multi-GPU environments without changes.

**Minimize host↔device transfers.** Each `.cpu()` or `.numpy()` call synchronizes the CUDA stream, slowing down performance. Batch your transfers; never do them inside a hot loop.

```python
# Bad: forces synchronization every step
for step in loop:
    loss_val = loss.item()   # blocks GPU

# Good: accumulate then log
if step % log_freq == 0:
    loss_val = loss.item()
```

**Use `torch.no_grad()` for all inference and validation.** This disables the autograd engine, cuts memory in half, and accelerates operations.

```python
with torch.no_grad():
    preds = model(x)
```

---

## 2. Model Definition & Schema Validation

**Inherit from `nn.Module` and register all parameters via `__init__`.**
Never store tensors as plain Python attributes — wrap them in `nn.Parameter` or use `register_buffer` for non-trainable state (e.g., running stats, positional encodings).

```python
class MyModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(128, 64)
        self.register_buffer("pos_enc", build_pos_enc())   # saved in state_dict, not trained
```

**Keep `forward()` pure.** Avoid in-place operations on leaf tensors and side effects that break compilation via `torch.compile` or serialization.

**Use `nn.Sequential` and container modules** (`nn.ModuleList`, `nn.ModuleDict`) so PyTorch tracks sub-module parameters for `.parameters()`, `.to(device)`, and saving.

**Pydantic-based Configuration & Shape Documentation**
Standardize architecture parameter validation using Pydantic, and always document tensor shape structures in docstrings:

```python
from pydantic import BaseModel, Field

class TrainingConfig(BaseModel):
    batch_size: int = Field(default=64, gt=0)
    learning_rate: float = Field(default=1e-3, gt=0)
    device: str = "cuda" if torch.cuda.is_available() else "cpu"

def forward(self, x: torch.Tensor) -> torch.Tensor:
    """
    Args:
        x: Input tensor of shape (Batch, Channels, Height, Width)
    Returns:
        Logits: Tensor of shape (Batch, NumClasses)
    """
    # ...
```

---

## 3. Training Loop Essentials & Gradient Accumulation

Strict isolation between **Data Access (Datasets)**, **Model Definition (nn.Module)**, and **Execution Logic (Training Loops)** is non-negotiable.

### Processing Optimization Checklist
| Feature | Implementation Rule | Performance Impact |
| :--- | :--- | :--- |
| **AMP** | Use modern `torch.amp.autocast` + `GradScaler` | 2x - 3x Speedup on Tensor Cores |
| **Compilation** | Apply `torch.compile(model)` to fuse kernels | Substantial reduction in eager mode overhead |
| **Grad Reset** | `optimizer.zero_grad(set_to_none=True)` | Bypasses memory-memset read overhead |
| **Data Transfer** | `x.to(device, non_blocking=True)` | Overlaps CPU-GPU asynchronous communication |

### Minimum Correct Training Loop Structure:
```python
model.train()
optimizer.zero_grad(set_to_none=True)  # clear before forward, not after backward
output = model(batch)
loss = criterion(output, target)
loss.backward()
torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # stability
optimizer.step()
scheduler.step()               # after optimizer.step()
```

**Key training loop rules:**
- Call `model.train()` before training, `model.eval()` before validation — this toggles dropout and batch norm behavior.
- `zero_grad(set_to_none=True)` is faster than `zero_grad()` (skips manual zeroing memory writes).
- Always clip gradients when training deep architectures (e.g. transformers or RNNs).
- `scheduler.step()` goes **after** `optimizer.step()`, and after each epoch (or each step for warmup schedulers) depending on the scheduler type.

### Gradient Accumulation Notes
When GPU memory (VRAM) limits your maximum batch size, use gradient accumulation to simulate a larger batch size:

```
effective_batch_size = batch_size × grad_accum_steps
```

- **Rule**: Divide the loss by `grad_accum_steps` *before* calling `.backward()`. This keeps gradient magnitudes mathematically consistent regardless of accumulation depth.
- **Rule**: Only unscale and clip gradients when you actually execute `optimizer.step()`.

> [!NOTE]
> Detailed structural examples for end-to-end training pipelines, including AMP integration, `@dataclass` configs, and `torch.compile` usage, are documented in `examples/training_pipeline.py` and `references/training-loop.md`.


---

## 4. Data Loading

**Use `DataLoader` with `num_workers > 0` and `pin_memory=True` on GPU.**

```python
from torch.utils.data import DataLoader

loader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True,
    num_workers=4,          # 4–8 typical; use os.cpu_count() // 2 as a heuristic
    pin_memory=True,        # faster Host-to-Device transfer on CUDA
    persistent_workers=True # avoids worker process restart overhead across epochs
)
```

- **Implement `__len__` and `__getitem__` in custom Datasets.** Apply augmentations inside `__getitem__` so they run in multi-process worker pools, not the main process thread.
- **Normalize in the Dataset, not the model.** This keeps the model's `forward()` clean and lets you pre-normalize cached data.
- **Use `collate_fn` for variable-length sequences** instead of manual padding inside the Dataset.

---

## 5. Memory Management & Hidden State Detachment

**Delete intermediates and empty the cache when debugging Out-Of-Memory (OOM) errors.**
```python
del intermediate_tensor
torch.cuda.empty_cache()    # releases cached but unused memory back to OS
```

- **Use gradient checkpointing for very deep models** (`torch.utils.checkpoint`) — trades compute for memory by recomputing activations on the backward pass.
- **Mixed precision training (AMP) cuts memory ~2× and speeds up on Tensor Core GPUs:**
  - **`float16` (standard GPUs)**: Requires `GradScaler` to prevent gradient underflow:
    ```python
    scaler = torch.amp.GradScaler()
    with torch.amp.autocast(device_type="cuda", dtype=torch.float16):
        output = model(batch)
        loss = criterion(output, target)
    scaler.scale(loss).backward()
    scaler.step(optimizer)
    scaler.update()
    ```
  - **`bfloat16` (Ampere+ e.g., A100, H100)**: Does not suffer from the same range limitation; **no `GradScaler` is required**:
    ```python
    with torch.amp.autocast(device_type="cuda", dtype=torch.bfloat16):
        output = model(batch)
        loss = criterion(output, target)
    loss.backward()  # no scaling or unscaling necessary
    ```

- **RNN / Transformer Hidden State Detachment**: When carrying hidden state across chunks (Truncated Backpropagation Through Time - TBPTT), always detach it to prevent the graph from growing indefinitely across sequence chunks:
```python
hidden = hidden.detach()     # break computational graph between chunks
output, hidden = rnn(chunk, hidden)
```
> [!CAUTION]
> Failing to detach carried-over hidden states causes severe memory leaks as the graph keeps accumulating gradients across training steps, eventually leading to a certain out-of-memory (OOM) crash.

- **Profile before optimizing.** Use `torch.profiler` to find the actual bottleneck before rewriting code. See `references/performance.md`.


---

## 6. Reproducibility

Always seed everything at the top of a training script to guarantee reproducible results:

```python
import random
import numpy as np
import torch

def seed_everything(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False   # must be False for determinism
```

> [!TIP]
> `torch.backends.cudnn.benchmark = True` speeds up training with fixed input sizes but breaks reproducibility. Use it in production inference or stable deployment, not research experiments.

---

## 7. Saving & Loading

**Save `state_dict`, not the whole model object.** Pickling the model object breaks when class definitions or folder structures change.

```python
# Save complete checkpoint state
torch.save({
    "epoch": epoch,
    "model_state_dict": model.state_dict(),
    "optimizer_state_dict": optimizer.state_dict(),
    "loss": loss,
}, "checkpoint.pt")

# Load state dictionary securely
checkpoint = torch.load("checkpoint.pt", map_location=device)
model.load_state_dict(checkpoint["model_state_dict"])
optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
```

**Always pass `map_location`** so checkpoints saved on GPU load cleanly on CPU (and vice versa).

---

## 8. Common Pitfalls Checklist

| Pitfall | Fix |
|---|---|
| Forgot `model.eval()` at validation | Add `model.eval()` + `torch.no_grad()` block |
| Loss not decreasing | Check label dtype (`long` for CrossEntropy), check `zero_grad` placement |
| OOM on large batch | Use AMP, gradient checkpointing, or reduce batch size |
| `RuntimeError: inplace op on leaf` | Avoid `tensor[...] +=` on `requires_grad=True` leaves |
| Non-deterministic results | Set seeds; set `deterministic=True` |
| Slow data loading | Increase `num_workers`; use `pin_memory`; profile with `torch.profiler` |
| NaN loss | Clip gradients; check for log(0) or division by zero; use AMP scaler |
| `state_dict` key mismatch on load | Use `strict=False` and inspect missing/unexpected keys |
| Accumulating computation graph in a loop | Call `.detach()` on carried-over tensors (e.g., hidden states in RNNs) |

---

## 9. Code Style Conventions

- Type-annotate tensor shapes in comments: `# (B, T, C)` where B = Batch size, T = Sequence length, C = Channel/Feature dimension.
- Use `einops` for readable reshape, transpose, and reduction operations in complex architectures.
- Prefer functional calls where performance-equivalent: `F.cross_entropy(logits, labels)` over `nn.CrossEntropyLoss()(...)` in functional layers.
- Name tensors semantically: `logits`, `embeddings`, `attn_weights` — not `x1`, `out2`.
- Keep training scripts, model definitions, and dataset classes in separate files.

---

## 10. CPU Performance Optimization


- **Intra-op Parallelism**: Control the number of CPU threads used by PyTorch using `torch.set_num_threads(N)` to prevent thrashing and improve small-batch latency (default is all physical cores).
- **Environment variables**: Setting `OMP_NUM_THREADS` and `MKL_NUM_THREADS` bounds performance for numpy and math library operations.
- **Intel MKL-DNN acceleration**: On Intel hardware, ensure MKL-DNN is enabled (on by default: `torch.backends.mkldnn.enabled = True`).
- **Dynamic Quantization**: Reduce model size by ~4x and accelerate inference on CPU using dynamic int8 quantization of linear and LSTM layers:
```python
quantized_model = torch.quantization.quantize_dynamic(
    model, {torch.nn.Linear, torch.nn.LSTM}, dtype=torch.qint8
)
```

---

## Reference Files

Refer to the `references/` and `examples/` directories for highly performant and production-ready implementations:

- **[training-loop.md](references/training-loop.md)** — Production PyTorch training loop template using standard Python `@dataclass` configs, AMP autocast timing, gradient accumulation logic, validation runs, checkpoint saves/reloads, and recurrent hidden state detaching.
- **[performance.md](references/performance.md)** — Deep-dive optimization guide detailing `torch.profiler` workflows, `torch.compile` modes (e.g. `reduce-overhead`, `max-autotune`) with `fullgraph=True`, `float16`/`bfloat16` precision recap, launch processes for multi-GPU scaling (DDP), ONNX runtime inference optimization, batched inference patterns, and CPU threads/quantization.
- **[training_pipeline.py](examples/training_pipeline.py)** — Production-grade end-to-end executable pipeline exemplifying validated configurations, standard seeding, fused optimizers, and clean separation of concerns.