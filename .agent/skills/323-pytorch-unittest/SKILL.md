---
name: 323-pytorch-unittest
description: >
  Best practices for writing unit tests for PyTorch code. Use this skill whenever
  you are writing, reviewing, or debugging tests that involve PyTorch tensors,
  models, datasets, or training pipelines — including testing tensor values, shapes,
  dtypes, device placement, gradients (autograd), model determinism, and AMP.
  Trigger for any test file that imports torch, tests nn.Module components, or
  any time someone asks "how do I test this PyTorch function". Also use when reviewing
  existing tests that use plain `assert` or `==` on tensors, as these are
  likely incorrect and should be replaced.
tags:
  - python
  - pytorch
  - unit-testing
  - pytest
  - deep-learning
capabilities:
  actions:
    - assert_tensor_equality
    - test_shape_and_dtype
    - configure_tolerances
    - fix_random_seeds
    - test_gradients_and_autograd
    - test_device_placement
    - assert_model_determinism
  file_extensions:
    - .py
    - .ipynb
triggers:
  verbs:
    - test
    - assert
    - verify
    - mock
    - validate
  nouns:
    - pytest
    - unittest
    - assert_close
    - tolerance
    - seed
    - autograd
    - nn.Module
    - Tensor
manifest:
  knowledge_base:
    - references/ci-and-coverage.md
    - references/test-templates.md
---

# PyTorch Unit Testing Skill (Skill 323_unittest)

This skill details mandatory architecture for writing robust, thorough, and highly maintainable unit tests for PyTorch operations, leveraging `pytest` and `torch.testing`.

---

## 1. High-Performance Assertion Patterns
Strict validation of **value calculations**, **dimension preservation**, **data type stability**, **device placement**, and **gradient flow** is mandatory.

### Testing Best Practices Checklist
| Test Constraint | Implementation Rule | Rationale |
| :--- | :--- | :--- |
| **Value Assertions** | Never use plain `assert a == b` or `==` comparisons; use `torch.testing.assert_close` | Standard equality creates boolean tensors and fails to evaluate truth values properly |
| **Tolerance Rules** | Explicitly define `rtol` and `atol` for floats; document the justification in comments | Avoids precision failures due to platform-specific floating-point arithmetic (especially with AMP/CUDA) |
| **Shape & Dtype** | Assert shapes (`.shape`) and exact types (`.dtype`) as first-class properties | Catches silent matrix reshaping bugs and automatic upcasts |
| **Device Consistency** | Verify operations preserve or correctly handle device placement (`.device`) | Prevents silent fallback to CPU or cross-device operations |
| **Isolated RNGs** | Set deterministic seeds for `torch`, `numpy`, and `random` within tests | Guarantees reproducible test behavior |
| **Gradient Flow** | Verify `.requires_grad` and `.grad` after `backward()` | Ensures autograd graphs are connected properly and gradients flow |

---

## 2. 🧩 Standard Assertions Guide

### Exact Tensor Comparisons
For boolean, integer, or string tensors where floating-point approximation errors do not occur:

```python
import torch

# Enforces exact element-by-element equality (also checks shape and dtype)
torch.testing.assert_close(actual, expected, rtol=0.0, atol=0.0)
```

### Floating-Point Comparisons
For real-valued float tensors, always perform tolerance-bounded comparisons:

```python
# GOOD — tolerant of machine precision fluctuations
torch.testing.assert_close(actual, expected, rtol=1e-5, atol=1e-8)
```

> [!WARNING]
> Do NOT use `torch.allclose(a, b)` and then `assert`. `torch.testing.assert_close` provides vastly superior error messages detailing the exact mismatch percentage and maximum deviation.

---

## 3. 🧪 Core Testing Paradigms

### A. Testing Shapes and Dtypes
Logic errors frequently pass value checks but fail shape or data type checks. Always test these properties explicitly:

```python
def test_dtype_and_shape_preservation():
    a = torch.ones((5, 5), dtype=torch.float32)
    result = my_transformer(a)
    
    assert result.shape == (5, 5), f"Shape corrupted: got {result.shape}"
    assert result.dtype == torch.float32, f"Silent upcasting detected: got {result.dtype}"
```

---

### B. Parametrization Over Devices and Dtypes
Ensure your functions behave identically under different input scales, precisions, and compute devices:

```python
import pytest
import torch

@pytest.fixture(params=["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"])
def device(request):
    return torch.device(request.param)

@pytest.mark.parametrize("shape", [(1,), (10, 5), (2, 3, 4)])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_invariant_dimensions(device, shape, dtype):
    x = torch.randn(shape, dtype=dtype, device=device)
    
    result = my_transformer(x)
    assert result.shape == shape
    assert result.dtype == dtype
    assert result.device == device
```

---

### C. Testing Gradient Flow (Autograd)
Always verify that gradients flow completely through your custom modules or loss functions:

```python
def test_gradient_flow():
    model = MyModel()
    x = torch.randn(1, 3, 224, 224, requires_grad=True)
    
    output = model(x)
    loss = output.sum()
    loss.backward()
    
    # Check that gradients exist and are not zero
    assert x.grad is not None
    assert not torch.all(x.grad == 0)
    
    # Check model parameters received gradients
    for param in model.parameters():
        assert param.grad is not None
        assert not torch.all(param.grad == 0)
```

---

### D. Testing Determinism
Ensure your models or operations behave identically given the same random seed:

```python
def test_determinism():
    torch.manual_seed(42)
    model1 = MyModel()
    out1 = model1(torch.ones(1, 10))
    
    torch.manual_seed(42)
    model2 = MyModel()
    out2 = model2(torch.ones(1, 10))
    
    torch.testing.assert_close(out1, out2)
```

---

## 4. 🧪 Best Practices for OOM and Performance Testing
Trap memory leaks and unexpected graph accumulations in tests:

```python
def test_no_memory_leak():
    if not torch.cuda.is_available():
        pytest.skip("CUDA not available")
        
    model = MyModel().cuda()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    
    torch.cuda.reset_peak_memory_stats()
    initial_mem = torch.cuda.max_memory_allocated()
    
    for _ in range(5):
        optimizer.zero_grad()
        out = model(torch.randn(16, 3, 32, 32, device="cuda"))
        loss = out.sum()
        loss.backward()
        optimizer.step()
        
    final_mem = torch.cuda.max_memory_allocated()
    # Ensure memory doesn't grow unbounded over iterations
    assert final_mem < initial_mem * 1.5 
```

---

## 5. Manifest & Reference Files

Refer to the `references/` directory for highly performant and production-ready PyTorch testing implementations:

* **[ci-and-coverage.md](references/ci-and-coverage.md)** — Comprehensive guide for configuring pytest, CI pipelines, coverage thresholds, test markers (e.g. `@pytest.mark.gpu`), and debugging flaky or non-deterministic tests.
* **[test-templates.md](references/test-templates.md)** — Copy-pasteable test templates for testing CNNs, Transformer attention layers, custom loss functions, training loop logic, and snapshot/regression setups.
