# Reference: Production PyTorch Training Loop

A complete, annotated training loop incorporating all best practices. Use this as a template for new training scripts.

---

## Full Training Script Template

```python
import os
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.cuda.amp import GradScaler
from pathlib import Path
from dataclasses import dataclass


# ──────────────────────────────────────────────
# 0. Reproducibility
# ──────────────────────────────────────────────
def seed_everything(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ──────────────────────────────────────────────
# 1. Config (prefer dataclasses or argparse)
# ──────────────────────────────────────────────
@dataclass
class TrainConfig:
    seed: int = 42
    epochs: int = 50
    batch_size: int = 64
    lr: float = 3e-4
    weight_decay: float = 1e-2
    grad_clip: float = 1.0
    grad_accum_steps: int = 1       # effective batch = batch_size × grad_accum_steps
    amp: bool = True                # mixed precision
    checkpoint_dir: Path = Path("checkpoints")
    early_stop_patience: int = 10
    log_every: int = 100            # steps


# ──────────────────────────────────────────────
# 2. Setup
# ──────────────────────────────────────────────
def train(cfg: TrainConfig) -> None:
    seed_everything(cfg.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    # -- Model, optimizer, scheduler --
    model = MyModel().to(device)
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=cfg.epochs
    )
    criterion = nn.CrossEntropyLoss()
    scaler = GradScaler(enabled=cfg.amp)

    # -- Data --
    train_loader = DataLoader(
        train_dataset,
        batch_size=cfg.batch_size,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
        drop_last=True,             # avoids tiny last batch messing with BatchNorm
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=cfg.batch_size * 2,   # no grad → can use larger batch
        shuffle=False,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
    )

    # ──────────────────────────────────────────
    # 3. Training loop
    # ──────────────────────────────────────────
    best_val_loss = float("inf")
    patience_counter = 0
    global_step = 0

    for epoch in range(cfg.epochs):
        # ── Train ──
        model.train()
        train_loss_accum = 0.0

        for step, (inputs, labels) in enumerate(train_loader):
            inputs = inputs.to(device, non_blocking=True)   # non_blocking with pin_memory
            labels = labels.to(device, non_blocking=True)

            # Mixed precision forward
            with torch.autocast(device_type=device.type, dtype=torch.float16,
                                 enabled=cfg.amp):
                logits = model(inputs)                       # (B, num_classes)
                loss = criterion(logits, labels)
                loss = loss / cfg.grad_accum_steps           # scale for accumulation

            scaler.scale(loss).backward()

            # Gradient accumulation: only step every N mini-batches
            if (step + 1) % cfg.grad_accum_steps == 0:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), cfg.grad_clip
                )
                scaler.step(optimizer)
                scaler.update()
                optimizer.zero_grad(set_to_none=True)        # faster than zero_grad()
                global_step += 1

            train_loss_accum += loss.item() * cfg.grad_accum_steps

            if global_step % cfg.log_every == 0:
                avg = train_loss_accum / (step + 1)
                print(f"Epoch {epoch} | Step {global_step} | loss {avg:.4f}")

        # ── Validate ──
        val_loss = evaluate(model, val_loader, criterion, device, cfg)

        # scheduler steps once per epoch (for epoch-level schedulers)
        scheduler.step()

        print(f"Epoch {epoch} complete | val_loss {val_loss:.4f}")

        # ── Checkpointing ──
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            save_checkpoint(model, optimizer, epoch, val_loss, cfg)
        else:
            patience_counter += 1
            if patience_counter >= cfg.early_stop_patience:
                print(f"Early stopping at epoch {epoch}")
                break


# ──────────────────────────────────────────────
# 4. Evaluation
# ──────────────────────────────────────────────
@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    cfg: TrainConfig,
) -> float:
    model.eval()
    total_loss = 0.0

    for inputs, labels in loader:
        inputs = inputs.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        with torch.autocast(device_type=device.type, dtype=torch.float16,
                             enabled=cfg.amp):
            logits = model(inputs)
            loss = criterion(logits, labels)

        total_loss += loss.item()

    return total_loss / len(loader)


# ──────────────────────────────────────────────
# 5. Checkpointing
# ──────────────────────────────────────────────
def save_checkpoint(
    model: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
    val_loss: float,
    cfg: TrainConfig,
) -> None:
    path = cfg.checkpoint_dir / f"best.pt"
    torch.save(
        {
            "epoch": epoch,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "val_loss": val_loss,
            "config": cfg,
        },
        path,
    )
    print(f"  ✓ Checkpoint saved to {path}")


def load_checkpoint(
    path: str | Path,
    model: nn.Module,
    optimizer: torch.optim.Optimizer | None = None,
    device: torch.device | None = None,
) -> dict:
    device = device or torch.device("cpu")
    checkpoint = torch.load(path, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    if optimizer is not None:
        optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
    return checkpoint
```

---

## Gradient Accumulation Notes

When GPU memory is too small for the desired effective batch size:

```
effective_batch_size = batch_size × grad_accum_steps
```

Divide the loss by `grad_accum_steps` *before* `.backward()`. This keeps gradient magnitudes consistent regardless of accumulation depth. Clip gradients only when you actually call `optimizer.step()`.

---

## RNN / Transformer Hidden State Detachment

When carrying hidden state across chunks (TBPTT), always detach to prevent the graph from growing across chunks:

```python
hidden = hidden.detach()     # break computational graph between chunks
output, hidden = rnn(chunk, hidden)
```

Failing to detach causes memory leaks and eventually OOM.
