# Reference: CI, Coverage, and Test Configuration

---

## Table of Contents
1. pytest.ini / pyproject.toml configuration
2. Test markers (fast/slow/gpu)
3. Coverage setup
4. GitHub Actions CI pipeline
5. Test speed budgets
6. Debugging flaky tests

---

## 1. pytest Configuration

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short -p no:warnings"
markers = [
    "slow: marks tests as slow (deselect with '-m not slow')",
    "gpu: requires CUDA GPU",
    "integration: end-to-end tests",
]
filterwarnings = [
    "error",               # treat warnings as errors
    "ignore::DeprecationWarning",
]
```

---

## 2. Test Markers

Tag tests by speed and hardware requirements:

```python
import pytest

@pytest.mark.slow
def test_full_training_convergence():
    ...   # runs only with: pytest -m slow

@pytest.mark.gpu
def test_cuda_kernel():
    if not torch.cuda.is_available():
        pytest.skip("GPU not available")
    ...

@pytest.mark.integration
def test_end_to_end_pipeline():
    ...
```

**Run subsets in CI:**
```bash
# Fast tests only (< 30s total) — every commit
pytest -m "not slow and not integration"

# All tests including slow — nightly / pre-merge
pytest

# GPU tests only — on GPU runner
pytest -m gpu
```

---

## 3. Coverage

```toml
# pyproject.toml
[tool.coverage.run]
source = ["src"]
omit = ["src/experiments/*", "src/scripts/*"]
branch = true           # measure branch coverage, not just line coverage

[tool.coverage.report]
fail_under = 80         # fail CI if coverage drops below 80%
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

```bash
# Run tests with coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# View HTML report
open htmlcov/index.html
```

**Coverage targets by layer:**
| Layer | Target |
|---|---|
| Utility functions | 95%+ |
| Loss functions | 90%+ |
| Model layers | 80%+ |
| Training loop | 70%+ |
| Data pipelines | 75%+ |

---

## 4. GitHub Actions CI Pipeline

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  test-cpu:
    name: CPU Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run fast tests
        run: |
          pytest -m "not slow and not gpu and not integration" \
            --cov=src --cov-report=xml -q

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml

  test-gpu:
    name: GPU Tests
    runs-on: [self-hosted, gpu]    # your GPU runner label
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run GPU tests
        run: pytest -m "gpu or slow" -q

  test-nightly:
    name: Full Test Suite
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install -e ".[dev]"
      - name: Run all tests
        run: pytest --cov=src --cov-report=xml -q
```

---

## 5. Test Speed Budgets

Keeping tests fast prevents the habit of skipping them.

| Suite | Target time | Runs when |
|---|---|---|
| Unit + layer tests | < 15s | Every save (watch mode) |
| Full CPU suite | < 60s | Every commit |
| Slow CPU tests | < 5 min | PR / pre-merge |
| GPU tests | < 10 min | Main branch push |
| Integration tests | < 30 min | Nightly |

**Tips for keeping tests fast:**
- Use `hidden_dim=16`, `num_layers=1`, `seq_len=8` for model fixtures
- Avoid `DataLoader` with workers in unit tests — use direct indexing
- Mock filesystem I/O with `tmp_path`
- Use `@pytest.mark.parametrize` instead of loops inside tests

**Watch mode for TDD:**
```bash
pip install pytest-watch
ptw -- -m "not slow and not gpu" -q
```

---

## 6. Debugging Flaky Tests

Flaky ML tests are almost always caused by non-determinism. Diagnose with:

```bash
# Run a test 10 times to confirm it's flaky
pytest tests/test_model.py::test_output_shape --count=10
# requires: pip install pytest-repeat

# Run in random order to expose order dependencies
pytest --randomly-seed=last
# requires: pip install pytest-randomly
```

**Common flakiness causes and fixes:**

| Cause | Fix |
|---|---|
| Missing `torch.manual_seed` | Add seed fixture with `autouse=True` |
| Asserting exact loss values | Assert direction/range, not exact values |
| `model.train()` bleeding into eval | Call `model.eval()` explicitly in each test |
| Worker race conditions in DataLoader | Use `num_workers=0` in tests |
| Tolerance too tight for float16 | Use `atol=1e-3` for half-precision comparisons |
| CUDA context shared between tests | Add `torch.cuda.empty_cache()` in teardown |

```python
# Teardown for GPU tests
@pytest.fixture(autouse=True)
def clear_cuda_cache():
    yield
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
```
