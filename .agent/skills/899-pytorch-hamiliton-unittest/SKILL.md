---
name: 899-pytorch-hamiliton-unittest
description: High-performance unit testing suite for the vectorized PyTorch Markov Regime-Switching (MRS) model and Hamilton Filter. Validates tensor shapes, reparameterization constraints, and regime alignment sorting using Pytest.
tags:
  - python
  - pytorch
  - pytest
  - unit-testing
  - hamilton-filter
  - regime-switching
capabilities:
  actions:
    - test_parameter_reparameterization
    - test_hamilton_filter_shapes
    - test_regime_identifiability
    - test_prediction_step
  file_extensions:
    - .py
    - .json
    - .md
triggers:
  verbs:
    - test
    - assert
    - validate
    - verify
  nouns:
    - Pytest
    - Assertion
    - UnitTest
    - Fixture
    - NLL
manifest:
  knowledge_base:
    - assets/manifest.json
    - assets/test_metadata.json
  logic_examples:
    - examples/test_mrs_model.py
---

# Pytest Unit Testing for Vectorized Hamilton Filter & Markov Regime-Switching Model (Skill 899 Unittest)

This skill enforces rigorous unit testing frameworks for financial regime-switching models. Robust mathematical models require strict assertion audits of probability distributions, parameter constraints, and tensor transformations.

---

## 1. Unit Testing Core Architectural Principles

When writing unit tests for Markov Regime-Switching models and filters, three mathematical invariants must always be verified:

1. **Reparameterization Validity:** Raw backpropagated elements must be mapped to valid domains ($\sigma > 0$ and stochastic transition matrices where rows sum to exactly $1.0$).
2. **Filtered Probability Bounds:** At every step $t$ in time $T$, the filtered state assignment probabilities $P(S_t = k \mid Y_t)$ must form a valid probability distribution (non-negative and sum to exactly $1.0$ across the state dimension).
3. **Identifiability Permutation Equivariance:** When sorting parameters (to map state indices to specific regimes like Bull/Bear), all parameters—including multi-dimensional transition arrays—must undergo identical permutations to remain mathematically coherent.

---

## 2. 🧪 Test Checklist & Assertion Matrix

Always ensure your unit tests cover the following parameters:

| Feature | Assertion Rule | Pytest Validation Technique |
| :--- | :--- | :--- |
| **Float Precision** | High-precision comparison (`float64`) | `pytest` fixture with `torch.set_default_dtype(torch.float64)` |
| **State Distribution** | Sums to $1.0$ across dimension | `torch.allclose(probs.sum(dim=-1), torch.ones(...))` |
| **Domain Safety** | Strict boundaries ($\ge 0$ or $>0$) | `assert torch.all(sigma > 0)` |
| **Identifiability** | State parameters strictly ordered | `assert all(mu[i, j] >= mu[i, j+1])` |
| **Input Constraints** | Dimension alignment check | `pytest.raises(AssertionError)` on incorrect shapes |

---

## 3. Verifying Permutation Equivariance in Transition Tensors

To verify that state parameter sorting does not corrupt transition logic, tests must track a permutation mapping $perm$ on a 3D matrix. For any time series $i$, the transition matrix $P_i$ elements must follow:
$$P'_{i, j, k} = P_{i, \pi_i(j), \pi_i(k)}$$

Where $\pi_i(j)$ represents the index of the old state mapped to the new state index $j$.

```python
# Trace in unit test:
# If Series 0 sort order was State 1 -> State 2 -> State 0 (perm = [1, 2, 0])
# The new element at [0, 0] must match old element at [1, 1]
sorted_trans = model.raw_trans_mat.data
assert sorted_trans[0, 0, 0] == original_trans[0, perm[0], perm[0]]
```

---

## 4. How to Execute Unit Tests

The testing suite is designed using `pytest` and can be executed natively from the workspace root directory:

```bash
# Run the entire test suite with verbose output
pytest -v .agents/skills/899_pytorch_hamiliton_unittest/examples/test_mrs_model.py
```

> [!NOTE]
> The complete, high-precision test implementations validating each case described above are hosted inside `examples/test_mrs_model.py`.
