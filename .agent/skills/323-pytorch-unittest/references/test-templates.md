# Reference: PyTorch Test Templates

Copy-paste templates for common test scenarios.

---

## Table of Contents
1. CNN / image model tests
2. Transformer / attention layer tests
3. Custom loss function tests
4. Training loop mock tests
5. Regression tests (output snapshot)
6. Property-based tests with Hypothesis

---

## 1. CNN / Image Model Tests

```python
import pytest
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset


class TestCNN:
    """Test suite for a convolutional image classifier."""

    @pytest.fixture
    def model(self, device):
        return MyCNN(in_channels=3, num_classes=10).to(device)

    @pytest.fixture
    def batch(self, device):
        return torch.randn(8, 3, 32, 32, device=device)

    def test_output_shape(self, model, batch):
        out = model(batch)
        assert out.shape == (8, 10)

    def test_output_is_logits_not_probs(self, model, batch):
        """Logits should not sum to 1 across classes."""
        out = model(batch)
        prob_sums = out.softmax(dim=-1).sum(dim=-1)
        torch.testing.assert_close(prob_sums, torch.ones(8, device=out.device))
        # But raw logits definitely don't sum to 1
        assert not torch.allclose(out.sum(dim=-1), torch.ones(8, device=out.device))

    def test_no_nan_in_output(self, model, batch):
        out = model(batch)
        assert torch.isfinite(out).all(), "Output contains NaN or Inf"

    def test_batch_independence(self, model, device):
        """Output for sample i must not depend on sample j."""
        x = torch.randn(4, 3, 32, 32, device=device)
        full_out = model(x)

        for i in range(4):
            single_out = model(x[i:i+1])
            torch.testing.assert_close(single_out[0], full_out[i], atol=1e-5, rtol=1e-4)

    def test_gradients_flow_through_all_layers(self, model, batch, device):
        target = torch.randint(0, 10, (8,), device=device)
        loss = F.cross_entropy(model(batch), target)
        loss.backward()
        for name, param in model.named_parameters():
            assert param.grad is not None, f"No grad: {name}"

    def test_overfit_single_batch(self):
        torch.manual_seed(0)
        model = MyCNN(in_channels=3, num_classes=4)
        opt = torch.optim.Adam(model.parameters(), lr=1e-2)
        x = torch.randn(4, 3, 16, 16)
        y = torch.tensor([0, 1, 2, 3])

        for _ in range(300):
            opt.zero_grad(set_to_none=True)
            loss = F.cross_entropy(model(x), y)
            loss.backward()
            opt.step()

        assert loss.item() < 0.05
```

---

## 2. Transformer / Attention Layer Tests

```python
class TestMultiHeadAttention:

    @pytest.fixture
    def attn(self, device):
        return MyMultiHeadAttention(embed_dim=64, num_heads=4).to(device)

    def test_output_shape_self_attention(self, attn, device):
        x = torch.randn(2, 10, 64, device=device)   # (B, T, D)
        out, weights = attn(x, x, x)
        assert out.shape == (2, 10, 64)
        assert weights.shape == (2, 4, 10, 10)       # (B, H, T, T)

    def test_attention_weights_sum_to_one(self, attn, device):
        x = torch.randn(2, 8, 64, device=device)
        _, weights = attn(x, x, x)
        sums = weights.sum(dim=-1)    # sum over key dimension
        torch.testing.assert_close(sums, torch.ones_like(sums), atol=1e-5, rtol=0)

    def test_causal_mask_prevents_future_attention(self, device):
        """With a causal mask, position t must not attend to positions > t."""
        attn = MyMultiHeadAttention(embed_dim=32, num_heads=2, causal=True).to(device)
        x = torch.randn(1, 6, 32, device=device)
        _, weights = attn(x, x, x)        # weights: (1, 2, 6, 6)
        # Upper triangle (above diagonal) must be zero
        upper = torch.triu(weights[0, 0], diagonal=1)
        assert upper.abs().max().item() < 1e-6, "Causal mask leaks future information"

    def test_padding_mask_zeroes_attention(self, attn, device):
        x = torch.randn(2, 5, 64, device=device)
        # Mask out last 2 positions for the second sequence
        mask = torch.zeros(2, 5, dtype=torch.bool, device=device)
        mask[1, 3:] = True
        _, weights = attn(x, x, x, key_padding_mask=mask)
        # Masked positions should receive ~0 attention
        assert weights[1, :, :, 3:].abs().max().item() < 1e-5
```

---

## 3. Custom Loss Function Tests

```python
class TestFocalLoss:
    """Template for testing any custom loss function."""

    def test_reduces_to_cross_entropy_when_gamma_zero(self):
        pred = torch.randn(16, 5)
        target = torch.randint(0, 5, (16,))
        focal = FocalLoss(gamma=0.0, reduction="mean")
        ce = F.cross_entropy(pred, target, reduction="mean")
        torch.testing.assert_close(focal(pred, target), ce, atol=1e-5, rtol=1e-4)

    def test_loss_is_scalar(self):
        pred = torch.randn(8, 4)
        target = torch.randint(0, 4, (8,))
        loss = FocalLoss()(pred, target)
        assert loss.shape == torch.Size([])

    def test_loss_is_nonnegative(self):
        for _ in range(20):
            pred = torch.randn(16, 5)
            target = torch.randint(0, 5, (16,))
            assert FocalLoss()(pred, target).item() >= 0

    def test_loss_is_differentiable(self):
        pred = torch.randn(4, 3, requires_grad=True)
        target = torch.randint(0, 3, (4,))
        FocalLoss()(pred, target).backward()
        assert pred.grad is not None
        assert torch.isfinite(pred.grad).all()

    def test_well_classified_samples_contribute_less(self):
        """Focal loss should down-weight easy examples."""
        pred_easy = torch.tensor([[10.0, -10.0]])   # very confident, correct
        pred_hard = torch.tensor([[0.5, -0.5]])     # uncertain
        target = torch.tensor([0])
        loss_easy = FocalLoss(gamma=2.0)(pred_easy, target)
        loss_hard = FocalLoss(gamma=2.0)(pred_hard, target)
        assert loss_easy < loss_hard

    def test_class_weights_applied_correctly(self):
        weight = torch.tensor([2.0, 1.0, 1.0])
        pred = torch.randn(8, 3)
        target_class0 = torch.zeros(8, dtype=torch.long)
        target_class1 = torch.ones(8, dtype=torch.long)
        loss0 = FocalLoss(weight=weight)(pred, target_class0)
        loss1 = FocalLoss(weight=weight)(pred, target_class1)
        # Class 0 has 2× weight so its loss should generally be higher
        # (test the ratio, not absolute values)
        ratio = loss0.item() / (loss1.item() + 1e-8)
        assert 1.5 < ratio < 3.0, f"Unexpected weight ratio: {ratio:.2f}"
```

---

## 4. Training Loop Tests (with Mocking)

Test the training loop logic without a real model or dataset:

```python
from unittest.mock import MagicMock, patch
import torch.nn as nn


def test_optimizer_step_called_each_batch(mocker):
    """Verify optimizer.step() fires once per batch."""
    model = nn.Linear(4, 2)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    step_spy = mocker.spy(optimizer, "step")

    loader = [(torch.randn(8, 4), torch.randint(0, 2, (8,))) for _ in range(5)]
    train_one_epoch(model, loader, optimizer, nn.CrossEntropyLoss())

    assert step_spy.call_count == 5


def test_loss_decreases_over_epochs():
    """Loss should trend downward over 10 epochs on fixed data."""
    torch.manual_seed(0)
    model = nn.Linear(8, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)
    x = torch.randn(32, 8)
    y = torch.randint(0, 2, (32,))
    loader = [(x, y)]

    losses = []
    for _ in range(10):
        epoch_loss = train_one_epoch(model, loader, optimizer, nn.CrossEntropyLoss())
        losses.append(epoch_loss)

    assert losses[-1] < losses[0], f"Loss did not decrease: {losses[0]:.4f} → {losses[-1]:.4f}"


def test_scheduler_steps_after_optimizer(mocker):
    model = nn.Linear(4, 2)
    optimizer = torch.optim.Adam(model.parameters())
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=1)

    call_order = []
    mocker.patch.object(optimizer, "step", side_effect=lambda: call_order.append("opt"))
    mocker.patch.object(scheduler, "step", side_effect=lambda: call_order.append("sched"))

    run_training_step(model, optimizer, scheduler, ...)

    opt_idx = call_order.index("opt")
    sched_idx = call_order.index("sched")
    assert opt_idx < sched_idx, "scheduler.step() must come after optimizer.step()"
```

---

## 5. Regression / Snapshot Tests

Pin model outputs to catch unintended behavior changes across refactors:

```python
def test_output_regression(tmp_path):
    """Output must not change across refactors."""
    torch.manual_seed(42)
    model = MyModel()
    model.eval()
    x = torch.randn(2, 64)
    snapshot_path = Path("tests/snapshots/model_output.pt")

    with torch.no_grad():
        actual = model(x)

    if snapshot_path.exists():
        expected = torch.load(snapshot_path)
        torch.testing.assert_close(actual, expected, atol=1e-6, rtol=1e-5)
    else:
        # First run: create the snapshot (commit this file)
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(actual, snapshot_path)
        pytest.skip("Snapshot created — run again to validate")
```

**Commit snapshot files to version control.** Update them intentionally when you change
model architecture.

---

## 6. Property-Based Tests with Hypothesis

Hypothesis generates random inputs to find edge cases automatically:

```python
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.extra.numpy import arrays
import numpy as np


@given(
    batch_size=st.integers(min_value=1, max_value=32),
    seq_len=st.integers(min_value=1, max_value=64),
)
@settings(max_examples=20, deadline=5000)
def test_rnn_output_shape_is_always_correct(batch_size, seq_len):
    model = MyRNN(input_size=16, hidden_size=32)
    x = torch.randn(batch_size, seq_len, 16)
    out, hidden = model(x)
    assert out.shape == (batch_size, seq_len, 32)
    assert hidden.shape == (1, batch_size, 32)


@given(st.floats(min_value=-10, max_value=10, allow_nan=False, allow_infinity=False))
def test_activation_output_is_always_finite(value):
    x = torch.tensor([[value]])
    out = my_custom_activation(x)
    assert torch.isfinite(out).all()
```
