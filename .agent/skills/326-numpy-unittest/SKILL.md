---
name: 326-numpy-unittest
description: >
  Best practices for writing unit tests for NumPy code. Use this skill whenever
  you are writing, reviewing, or debugging tests that involve NumPy arrays —
  including testing array values, shapes, dtypes, NaN/Inf behavior, edge cases,
  mathematical invariants, or input mutation. Trigger for any test file that
  imports numpy, any pytest parametrize pattern over shapes or dtypes, or any
  time someone asks "how do I test this NumPy function". Also use when reviewing
  existing tests that use plain `assert` or `==` on arrays, as these are
  likely incorrect and should be replaced.
tags:
  - python
  - numpy
  - unit-testing
  - pytest
  - mathematical-invariants
capabilities:
  actions:
    - assert_array_equality
    - test_shape_and_dtype
    - configure_tolerances
    - fix_random_seeds
    - test_edge_cases
    - test_mathematical_invariants
    - assert_no_input_mutation
    - assert_errstate_warnings
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
    - assert_allclose
    - assert_array_equal
    - tolerance
    - seed
    - random_state
manifest:
  knowledge_base:
    - assets/unittest_metadata.json
    - assets/manifest.json
  logic_examples:
    - examples/test_numpy_pipeline.py
---

# NumPy Unit Testing Skill (Skill 326_unittest)

This skill details mandatory architecture for writing robust, thorough, and highly maintainable unit tests for NumPy operations, leveraging `pytest` and `numpy.testing`.

---

## 1. High-Performance Assertion Patterns
Strict validation of **value calculations**, **dimension preservation**, **data type stability**, and **side-effect bounds** is mandatory.

### Testing Best Practices Checklist
| Test Constraint | Implementation Rule | Rationale |
| :--- | :--- | :--- |
| **Value Assertions** | Never use plain `assert a == b` or `==` comparisons; use `numpy.testing` | Standard equality raises truth-value errors or checks reference identity |
| **Tolerance Rules** | Explicitly define `rtol` and `atol` for floats; document the justification in comments | Avoids precision failures due to platform-specific floating-point arithmetic |
| **Shape & Dtype** | Assert shapes (`.shape`) and exact types (`.dtype`) as first-class properties | Catches silent matrix reshaping bugs and automatic upcasts to `float64` |
| **Isolated RNGs** | Instantiate isolated `np.random.default_rng(seed=...)` within each test method | Bypasses global state pollution and guarantees reproducible test behavior |
| **Non-contiguous** | Verify functions work properly on transposed (`.T`) or strided slice views | Catches layout errors where code assumes contiguous memory blocks |
| **Zero Side-Effects**| Backup input, call function, and verify input remains unchanged | Ensures functions do not mutate parameters unless explicitly specified |

---

## 2. 🧩 Standard Assertions Guide

### Exact Array Comparisons
For boolean, integer, or string arrays where floating-point approximation errors do not occur:

```python
import numpy.testing as npt

# Enforces exact element-by-element equality
npt.assert_array_equal(actual, expected)
```

### Floating-Point Comparisons
For real-valued float arrays, always perform tolerance-bounded comparisons:

```python
# GOOD — tolerant of machine precision fluctuations
npt.assert_allclose(actual, expected, rtol=1e-5, atol=1e-8)
```

> [!WARNING]
> Do NOT use `np.testing.assert_array_almost_equal` — it is legacy. Use `npt.assert_allclose` which provides superior control over relative (`rtol`) and absolute (`atol`) boundaries.

---

## 3. 🧪 Core Testing Paradigms

### A. Testing Shapes and Dtypes
Logic errors frequently pass value checks but fail shape or data type checks. Always test these properties explicitly:

```python
def test_dtype_and_shape_preservation():
    a = np.ones((5, 5), dtype=np.float32)
    result = my_transformer(a)
    
    assert result.shape == (5, 5), f"Shape corrupted: got {result.shape}"
    assert result.dtype == np.float32, f"Silent upcasting detected: got {result.dtype}"
```

---

### B. Parametrization Over Shapes and Dtypes
Ensure your functions behave identically under different input scales and precisions:

```python
import pytest

@pytest.mark.parametrize("shape", [(1,), (10, 5), (2, 3, 4)])
@pytest.mark.parametrize("dtype", [np.float32, np.float64, np.int32])
def test_invariant_dimensions(shape, dtype):
    rng = np.random.default_rng(seed=42)
    x = rng.standard_normal(shape).astype(dtype)
    
    result = my_transformer(x)
    assert result.shape == shape
    assert result.dtype == dtype
```

---

### C. Testing Mathematical Invariants
When exact outputs are mathematically complex or depend on random state, verify mathematical invariants:

```python
# Row values sum to 1 (e.g. probabilities, softmax)
npt.assert_allclose(result.sum(axis=1), np.ones(result.shape[0]), rtol=1e-6)

# Monotonicity: Check that sorting order is preserved
assert np.all(np.diff(result) >= 0)

# Matrix symmetry
npt.assert_allclose(result, result.T, atol=1e-10)
```

---

## 4. 🧪 Error State Handling
Trap silent floating-point overflow, divide-by-zero, or invalid operations in tests using `np.errstate`:

```python
def test_divide_by_zero_handling():
    # Enforces floating-point errors to raise an exception inside this block
    with np.errstate(divide='raise', invalid='raise'):
        with pytest.raises(FloatingPointError):
            my_unstable_function(np.zeros(5))
```

---

## 5. Manifest & Logic Examples
Refer to the `assets/` and `examples/` directories for standardized configurations and comprehensive test suites:
* **Assets**: Refer to `assets/manifest.json` and `assets/unittest_metadata.json` for capabilities schemas and recommended default tolerances.
* **Logic Example**: Refer to `examples/test_numpy_pipeline.py` for a production-ready pytest file demonstrating:
  - Numerical correctness assertions with comment-justified tolerances.
  - Reproducible `np.random.default_rng` configurations.
  - Mathematical invariant and monotonicity testing.
  - Overflow checks and non-contiguous array strides verification.
  - Asserting the absence of unwanted input parameter mutations.