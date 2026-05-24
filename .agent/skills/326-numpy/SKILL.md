---
name: 326-numpy
description: >
  Best practices for writing correct, fast, and idiomatic NumPy code. Use this skill
  whenever you are writing, reviewing, or debugging NumPy code — including array
  creation, reshaping, indexing, broadcasting, mathematical operations, performance
  optimization, or interoperability with pandas/scipy/PyTorch. Trigger even for
  seemingly simple tasks like "sum an array" or "reshape a matrix", since subtle
  anti-patterns (Python loops, unintended copies, dtype mismatches) are easy to
  introduce without these guidelines.
tags:
  - python
  - numpy
  - numerical-computing
  - vectorization
  - matrix-operations
  - performance
capabilities:
  actions:
    - create_arrays
    - slice_index_arrays
    - vectorize_loops
    - broadcast_shapes
    - reshape_transpose
    - optimize_memory_dtype
    - stack_concatenate
    - generate_random_data
    - manipulate_axes
    - handle_nans_floats
    - sort_search_partition
    - perform_set_operations
    - persist_npy_npz_memmap
    - test_numpy_assertions
  file_extensions:
    - .py
    - .ipynb
    - .npy
    - .npz
triggers:
  verbs:
    - create
    - slice
    - index
    - vectorize
    - broadcast
    - reshape
    - transpose
    - stack
    - concatenate
    - split
    - sort
    - search
    - save
    - load
    - test
  nouns:
    - NumPy
    - ndarray
    - array
    - vectorization
    - broadcasting
    - dtype
    - axis
    - ufunc
    - einsum
    - memmap
    - assert_allclose
manifest:
  knowledge_base:
    - assets/numpy_metadata.json
    - assets/manifest.json
  logic_examples:
    - examples/high_performance_computation.py
---

# NumPy High-Performance Orchestration (Skill 326)

This skill enforces mandatory architecture for robust, enterprise-grade NumPy workflows focused on **zero-copy slicing**, **vectorized computations**, **memory-efficient broadcasting**, and **GIL-free parallelism**.

---

## 1. High-Performance Architectural Patterns
Strict separation between **Data Ingestion**, **Vectorized Core Computation**, and **State/Testing Validation** is non-negotiable.

### Mandatory Optimization Checklist
| Optimization | Implementation Rule | Performance Impact |
| :--- | :--- | :--- |
| **Vectorization** | Eliminate all Python loops over array elements; use NumPy `ufuncs` | 100x+ Speedup |
| **Explicit Dtypes** | Specify `dtype=` during creation to prevent automatic `float64` upcasting | 2x Memory & Speed Optimization |
| **Broadcasting** | Prefer `np.newaxis` / `None` over memory-allocating `np.repeat` or `np.tile` | Zero-copy dimension expansion |
| **Out parameter** | Pass `out=` to mathematical functions to reuse allocated array buffers | Bypasses intermediate allocations |
| **GIL Release** | Target C-level computations (FFT, dot products) using threadpools | Real multi-core CPU utilization |
| **Top-K Partition** | Use `np.argpartition` instead of a full `np.argsort` for top-k selections | Reduces complexity from O(N log N) to O(N) |

---

## 2. 🧩 Idiomatic NumPy Best Practices

### A. Array Creation & Casting
Avoid implicit type inference. Always specify the `dtype` explicitly to prevent silent bloat:

```python
# BAD — Implicit casting to float64/int64
a = np.array([1, 2, 3])

# GOOD — Explicit, size-controlled dtypes
a = np.array([1, 2, 3], dtype=np.int32)
```

Use modern, optimized factory functions for standard shape generation:
```python
np.zeros((m, n), dtype=np.float32)       # Zeros buffer
np.ones((m, n), dtype=np.float32)        # Ones buffer
np.empty((m, n), dtype=np.float32)       # Fastest: uninitialized memory allocation
np.linspace(start, stop, num)            # Evenly spaced floats (prefer over np.arange for float intervals)
```

> [!WARNING]
> Do NOT use `np.matrix` — it is deprecated. Use standard 2D `ndarray` arrays instead.

---

### B. Indexing, Slicing & Views
Understand the distinction between a memory view (zero-copy) and a physical copy:

| Operation | Result Type | Side-Effect Risk |
| :--- | :--- | :--- |
| **Basic Slicing** (`a[1:5]`) | **View** | Modifying the slice mutates the original array |
| **Fancy Indexing** (`a[[0, 2]]`) | **Copy** | Safe to modify; allocates new memory |
| **Boolean Indexing** (`a[a > 0]`) | **Copy** | Safe to modify; allocates new memory |

```python
# Unintentional mutation via slicing (view)
sub = arr[1:4]
sub[:] = 0  # Zeroes out index 1 to 3 in BOTH sub and arr!

# Safe isolation via explicit copy
sub_copy = arr[1:4].copy()
```

---

### C. Vectorized Broadcasting
Broadcasting enables element-wise operations on arrays with differing dimensions without copying data. The rule matches dimensions from the right; dimensions are compatible if they are equal, 1, or absent.

```python
# Broadcase row matrix (1, D) with column matrix (N, 1) -> (N, D) matrix
row = np.array([1, 2, 3])             # Shape (3,) -> treated as (1, 3)
col = np.array([[10], [20]])          # Shape (2, 1)

grid = col + row                      # Shape (2, 3) outer sum
```

Use `np.newaxis` or `None` to explicitly add dimensions rather than using `np.tile` or `np.repeat`, which allocate new memory buffers unnecessarily.

---

### D. Shape-Safe Feature Preparation
Ensure incoming inputs are consistently scaled, typed, and structured into a 2D matrix for estimators:

```python
import numpy as np
import numpy.typing as npt

def prepare_inference_matrix(
    raw_features: list[float] | list[list[float]]
) -> npt.NDArray[np.float64]:
    """
    Standardizes feature inputs into a validated 2D float64 NumPy array.
    Guarantees compatibility with Scikit-Learn estimators.
    """
    # Convert and align data types
    arr = np.asarray(raw_features, dtype=np.float64)
    
    # Standardize 1D input (single example) into a 2D matrix (1, N)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    elif arr.ndim > 2:
        raise ValueError(f"Expected 1D or 2D array, received {arr.ndim}D instead")
        
    return arr
```

---

### E. Vectorized Feature Engineering
Avoid loops by relying on NumPy select/where arrays for swift label mapping:

```python
import numpy as np

def label_feedback_vector(
    predictions: np.ndarray, 
    feedbacks: np.ndarray
) -> np.ndarray:
    """
    Transforms generic user feedback vectors into robust true training labels.
    - feedback == 1 (thumbs up) -> use predicted class
    - feedback == 0 (thumbs down) -> label is masked or needs manual true input
    """
    # 1 indicates Thumbs Up, 0 indicates Thumbs Down, -1 indicates No Feedback
    return np.where(feedbacks == 1, predictions, -1)
```

---

## 3. 🧪 Numerical Hygiene & Validation

### NaN and Infinity Propagation
Numerical values like `NaN` propagate silently and corrupt downstream calculations. Check for them explicitly:

```python
np.isnan(arr)                  # Element-wise boolean mask
np.any(np.isnan(arr))          # Rapid sanity check

# Use NaN-aware reductions to bypass missing entries
np.nansum(arr)
np.nanmean(arr)
np.nanmax(arr)
```

> [!CAUTION]
> Never check for NaN using equality comparison (`a == np.nan`), as NaN is never equal to itself. Use `np.isnan(a)`.

### Silent Integer Overflow
Unlike standard Python integers, NumPy fixed-precision integers wrap silently on overflow:

```python
# BAD — wraps around silently
a = np.array([127], dtype=np.int8)
a + 1  # Result: array([-128], dtype=np.int8)

# GOOD — explicit upcast before execution
a.astype(np.int32) + 1  # Result: array([128], dtype=np.int32)
```

---

## 4. 🧪 Robust Unit Testing

Never use standard `==` or plain assert statements to compare float arrays. Always use the specialized testing assertions in `numpy.testing`:

```python
import numpy.testing as npt

# Exact comparison for integer/boolean arrays
npt.assert_array_equal(actual, expected)

# Float comparisons with tolerance to account for machine precision
npt.assert_allclose(actual, expected, rtol=1e-5, atol=1e-8)
```

> [!NOTE]
> Floating-point equality is highly sensitive. Provide explanatory comments for your tolerance levels (`rtol`/`atol`) when utilizing iterative algorithms.

---

## 5. Manifest & Logic Examples
Refer to the `assets/` and `examples/` directories for highly performant and production-ready implementations:
* **Assets**: Refer to `assets/manifest.json` and `assets/numpy_metadata.json` for standardized schemas and capabilities metadata.
* **Logic Example**: Refer to `examples/high_performance_computation.py` for a fully production-ready pipeline utilizing:
  - Vectorized pairwise distance calculation with broadcasting.
  - O(N) top-k selection using `argpartition`.
  - Multi-threaded, GIL-free concurrent execution via `ThreadPoolExecutor`.
  - Pydantic-based configuration and explicit shape docstring annotations.
