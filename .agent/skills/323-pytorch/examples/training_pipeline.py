import os
import random
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from pydantic import BaseModel, Field
from typing import tuple

class TrainingConfig(BaseModel):
    """Pydantic configuration for high-performance training."""
    batch_size: int = Field(default=32, gt=0)
    learning_rate: float = Field(default=1e-3, gt=0)
    epochs: int = Field(default=5, gt=0)
    hidden_dim: int = Field(default=64, gt=0)
    num_workers: int = Field(default=2, ge=0)
    pin_memory: bool = True
    device: str = "cuda" if torch.cuda.is_available() else "cpu"
    seed: int = 42

def seed_everything(seed: int = 42):
    """Ensure reproducible training passes."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

class HighPerfDataset(Dataset):
    """Modern Dataset with explicit shape documentation."""
    def __init__(self, size: int = 100):
        self.size = size

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            x: Feature tensor of shape (10,)
            y: Label tensor of shape ()
        """
        # Return dummy deterministic tensors based on idx to prevent true randomness
        generator = torch.Generator().manual_seed(idx)
        x = torch.randn(10, generator=generator)
        y = torch.tensor(idx % 2, dtype=torch.long)
        return x, y

class OptimizedModel(nn.Module):
    """Modular model with standard Kaiming weight initialization."""
    def __init__(self, input_dim: int, hidden_dim: int, num_classes: int):
        super().__init__()
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        self.classifier = nn.Linear(hidden_dim, num_classes)
        self._init_weights()

    def _init_weights(self):
        """Standardize initialization for faster convergence."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor of shape (Batch, InputDim)
        Returns:
            Logits: Tensor of shape (Batch, NumClasses)
        """
        return self.classifier(self.feature_extractor(x))

def train_one_epoch(
    model: nn.Module, 
    loader: DataLoader, 
    optimizer: torch.optim.Optimizer, 
    criterion: nn.Module, 
    device: torch.device, 
    scaler: torch.amp.GradScaler
) -> float:
    """High-efficiency training loop using modern PyTorch AMP."""
    model.train()
    total_loss = 0.0
    use_amp = device.type == "cuda"

    for x, y in loader:
        # Non-blocking device transfer (overlaps CPU-to-GPU data transmission)
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        
        # Prevent read-overhead with set_to_none=True
        optimizer.zero_grad(set_to_none=True)
        
        # Mixed Precision Autocast
        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            output = model(x)
            loss = criterion(output, y)
        
        # Scaled Backward Pass
        scaler.scale(loss).backward()
        
        # Unscale for gradient clipping
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        
        scaler.step(optimizer)
        scaler.update()

        total_loss += loss.item()

    return total_loss / len(loader)

@torch.no_grad()
def evaluate(
    model: nn.Module, 
    loader: DataLoader, 
    criterion: nn.Module, 
    device: torch.device
) -> tuple[float, float]:
    """Efficient evaluation disabling autograd gradient tracking."""
    model.eval()
    total_loss = 0.0
    correct = 0
    use_amp = device.type == "cuda"

    for x, y in loader:
        x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
        
        with torch.amp.autocast(device_type=device.type, enabled=use_amp):
            output = model(x)
            loss = criterion(output, y)
        
        total_loss += loss.item()
        pred = output.argmax(dim=1)
        correct += (pred == y).sum().item()

    accuracy = correct / len(loader.dataset)
    return total_loss / len(loader), accuracy

def main():
    # 1. Load Pydantic Config & Seed
    config = TrainingConfig()
    seed_everything(config.seed)
    
    device = torch.device(config.device)
    print(f"Using execution device: {device}")
    
    # 2. Setup DataLoaders with Pinned Memory
    dataset = HighPerfDataset(128)
    loader = DataLoader(
        dataset, 
        batch_size=config.batch_size, 
        shuffle=True, 
        num_workers=config.num_workers, 
        pin_memory=config.pin_memory,
        persistent_workers=config.num_workers > 0
    )
    
    # 3. Model Definition & Compilation (if supported)
    model = OptimizedModel(10, config.hidden_dim, 2).to(device)
    if hasattr(torch, "compile") and device.type == "cuda":
        try:
            model = torch.compile(model, mode="reduce-overhead")
            print("Model successfully compiled with torch.compile!")
        except Exception as e:
            print(f"Compilation skipped or failed: {e}")
    
    # 4. Standardized Fused Optimizer Setup
    use_fused = device.type == "cuda"
    optimizer = torch.optim.AdamW(
        model.parameters(), 
        lr=config.learning_rate,
        fused=use_fused
    )
    
    criterion = nn.CrossEntropyLoss()
    scaler = torch.amp.GradScaler(enabled=device.type == "cuda")
    
    best_loss = float("inf")
    checkpoint_path = "model_best.pt"

    # 5. Epoch Iterations with Early Stopping checkpointing
    for epoch in range(config.epochs):
        train_loss = train_one_epoch(model, loader, optimizer, criterion, device, scaler)
        val_loss, val_acc = evaluate(model, loader, criterion, device)
        
        print(
            f"Epoch {epoch + 1:02d} | "
            f"Train Loss: {train_loss:.4f} | "
            f"Val Loss: {val_loss:.4f} | "
            f"Val Acc: {val_acc:.2%}"
        )
        
        # Save checkpoint if validation loss improves
        if val_loss < best_loss:
            best_loss = val_loss
            torch.save({
                "epoch": epoch + 1,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "loss": best_loss,
            }, checkpoint_path)
            print(f"--> Saved best checkpoint to {checkpoint_path}")

    # 6. Secure state_dict reloading demonstration
    if os.path.exists(checkpoint_path):
        print("\nDemonstrating checkpoint reloading:")
        checkpoint = torch.load(checkpoint_path, map_location=device)
        # Note: If compiled, load state_dict matching original module keys
        raw_model = OptimizedModel(10, config.hidden_dim, 2).to(device)
        raw_model.load_state_dict(checkpoint["model_state_dict"])
        print("--> Checkpoint state_dict loaded successfully.")
        
        # Clean up sandbox file
        try:
            os.remove(checkpoint_path)
        except OSError:
            pass

if __name__ == "__main__":
    main()
