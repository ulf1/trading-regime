# Reference: PyTorch Performance Optimization

Deep-dive guide for profiling, optimizing, and scaling PyTorch training and inference.

---

## Table of Contents
1. Profiling workflow
2. `torch.compile`
3. Mixed precision recap
4. Multi-GPU with DDP
5. Inference optimization (TorchScript, ONNX, TensorRT)
6. CPU performance

---

## 1. Profiling Workflow

**Always profile before optimizing.** Common bottleneck locations:
- Data loading (CPU-bound) — watch for DataLoader workers being at 100%
- GPU kernel launch overhead — many small ops
- Memory bandwidth — large tensor copies
- Synchronization points — `.item()`, `.numpy()`, print inside loop

### PyTorch Profiler (recommended)

```python
import torch
from torch.profiler import profile, record_function, ProfilerActivity

with profile(
    activities=[ProfilerActivity.CPU, ProfilerActivity.CUDA],
    schedule=torch.profiler.schedule(wait=1, warmup=1, active=3),
    on_trace_ready=torch.profiler.tensorboard_trace_handler("./log"),
    record_shapes=True,
    profile_memory=True,
    with_stack=True,
) as prof:
    for step, batch in enumerate(loader):
        train_step(batch)
        prof.step()
        if step >= 5:
            break

print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))
```

View in TensorBoard: `tensorboard --logdir ./log`

### Quick GPU utilization check
```bash
watch -n 0.5 nvidia-smi
# or for continuous metrics:
nvidia-smi dmon -s u -d 1
```

GPU utilization consistently < 70% → bottleneck is data loading or CPU preprocessing.

---

## 2. `torch.compile` (PyTorch 2.x)

`torch.compile` traces the model and emits optimized kernels via Triton. Typical speedup:
10–50% on modern GPUs for transformer workloads.

```python
model = torch.compile(model)              # default: "default" mode
model = torch.compile(model, mode="reduce-overhead")   # minimize kernel launch overhead
model = torch.compile(model, mode="max-autotune")      # max speed, longer compile time
```

**When to use:**
- Fixed input shapes (dynamic shapes possible but slower)
- Training loops that run for many iterations (amortize compile cost)
- PyTorch 2.0+ with CUDA 11.8+

**Caveats:**
- First forward pass is slow (compiles). Use warmup steps.
- Not compatible with all custom CUDA extensions.
- Use `fullgraph=True` to catch graph breaks (segments that fall back to eager).

```python
model = torch.compile(model, fullgraph=True)   # raises error on graph breaks
```

---

## 3. Mixed Precision (AMP) — Quick Recap

| dtype | Memory | Speed | Precision |
|---|---|---|---|
| float32 | 4 bytes | baseline | full |
| float16 | 2 bytes | 2–3× on Tensor Cores | reduced range (needs scaler) |
| bfloat16 | 2 bytes | 2–3× on Ampere+ | reduced mantissa, full range (no scaler needed) |

Prefer `bfloat16` on A100/H100 — no `GradScaler` required:

```python
import torch

with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
    output = model(x)
    loss = criterion(output, y)
loss.backward()    # no scaler needed with bfloat16
```

---

## 4. Multi-GPU: DistributedDataParallel (DDP)

**Prefer DDP over `DataParallel`** — DDP has one process per GPU, no GIL bottleneck, and scales linearly.

### Launch script

```bash
torchrun --nproc_per_node=4 train.py
```

### DDP setup inside `train.py`

```python
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader
from torch.utils.data.distributed import DistributedSampler

def setup_ddp():
    dist.init_process_group(backend="nccl")   # nccl for GPU, gloo for CPU
    rank = dist.get_rank()
    torch.cuda.set_device(rank)
    return rank

rank = setup_ddp()
device = torch.device(f"cuda:{rank}")

model = MyModel().to(device)
model = DDP(model, device_ids=[rank])

# Use DistributedSampler — handles per-rank data split
sampler = DistributedSampler(train_dataset)
loader = DataLoader(train_dataset, sampler=sampler, ...)

for epoch in range(epochs):
    sampler.set_epoch(epoch)    # required for proper shuffling across epochs
    ...

dist.destroy_process_group()
```

**Gradient sync**: DDP automatically all-reduces gradients during `.backward()`. No manual changes to the optimizer loop needed.

**Checkpoint on rank 0 only:**
```python
if rank == 0:
    save_checkpoint(model.module, ...)   # .module unwraps the DDP wrapper
```

---

## 5. Inference Optimization

### TorchScript (portable, no Python runtime)

```python
# Option A: tracing (faster, fixed input shapes)
example = torch.rand(1, 3, 224, 224).to(device)
scripted = torch.jit.trace(model, example)
torch.jit.save(scripted, "model.pt")

# Option B: scripting (supports control flow)
scripted = torch.jit.script(model)
torch.jit.save(scripted, "model.pt")

# Load anywhere (no class definition needed)
model = torch.jit.load("model.pt", map_location=device)
```

### ONNX Export

```python
torch.onnx.export(
    model,
    example_input,
    "model.onnx",
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}},
    opset_version=17,
)
```

Validate:
```python
import onnxruntime as ort
sess = ort.InferenceSession("model.onnx", providers=["CUDAExecutionProvider"])
out = sess.run(None, {"input": x.numpy()})
```

### Batched Inference Pattern

```python
@torch.no_grad()
def batch_inference(model, data, batch_size=256, device="cuda"):
    model.eval()
    results = []
    loader = DataLoader(data, batch_size=batch_size, shuffle=False,
                        num_workers=4, pin_memory=True)
    for batch in loader:
        batch = batch.to(device, non_blocking=True)
        with torch.autocast(device_type="cuda", dtype=torch.float16):
            out = model(batch)
        results.append(out.cpu())
    return torch.cat(results)
```

---

## 6. CPU Performance

- Use `torch.set_num_threads(N)` to control intra-op parallelism (default: all cores, which can hurt throughput for small batches)
- `OMP_NUM_THREADS` and `MKL_NUM_THREADS` env vars matter for numpy-adjacent ops
- For Intel CPUs, `torch.backends.mkldnn.enabled = True` (on by default) enables MKL-DNN
- Consider `torch.quantization.quantize_dynamic` for CPU inference: int8 weights, ~4× memory reduction

```python
import torch.nn as nn

quantized = torch.quantization.quantize_dynamic(
    model, {nn.Linear, nn.LSTM}, dtype=torch.qint8
)
```
