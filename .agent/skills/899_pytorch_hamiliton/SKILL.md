---
name: pytorch_hamiliton
description: High-performance vectorized Markov Regime-Switching (MRS) model engineering in PyTorch. Expert instructions for implementing batched Hamilton Filters, handling mathematical constraints (exponential/softmax transformations), and solving the regime label-switching problem.
tags:
  - python
  - pytorch
  - markov-regime-switching
  - hamilton-filter
  - time-series
  - vectorization
capabilities:
  actions:
    - scaffold_mrs_model
    - vectorize_hamilton_filter
    - estimate_regime_probabilities
    - predict_regime_transitions
  file_extensions:
    - .py
    - .json
    - .md
triggers:
  verbs:
    - filter
    - switch
    - estimate
    - predict
    - vectorize
  nouns:
    - Hamilton
    - Regime
    - Markov
    - NLL
    - Transition
manifest:
  knowledge_base:
    - assets/manifest.json
    - assets/mrs_metadata.json
  logic_examples:
    - examples/mrs_model.py
---

# Batched PyTorch Hamilton Filter & Markov Regime-Switching Model (Skill 899)

This skill enforces high-performance mathematical modeling of financial regime-switching patterns using **vectorized tensor calculations**, **constrained parameters**, and **automatic differentiation**.

## 1. Mathematical Reparameterization & Constraints

In a Markov Regime-Switching (MRS) model with $K$ states and $N$ parallel time series, all estimated parameters must stay mathematically valid throughout backpropagation. Ad-hoc optimization algorithms (like EM) are replaced with direct parameter transformations within the `nn.Module`.

| Parameter | Domain Constraint | Implementation Rule |
| :--- | :--- | :--- |
| **Standard Deviation ($\sigma_{i, k}$)** | Strictly Positive ($\sigma > 0$) | $\sigma_{i, k} = \exp(\text{raw\_sigma}_{i, k})$ |
| **Transition Probabilities ($P_{i, j, k}$)** | Stochastic Vector ($\sum_{k} P_{i, j, k} = 1, P \ge 0$) | $P_{i, j} = \text{softmax}(\text{raw\_trans\_mat}_{i, j}, \text{dim}=2)$ |

> [!IMPORTANT]
> Standard optimization uses raw parameters $\in \mathbb{R}$. Constraints must be applied on the forward pass using `get_constrained_params()` to ensure backpropagation is fully differentiable.

---

## 2. Fully Vectorized Hamilton Filtering

Rather than iterating over the batch dimension (time series) with a Python loop, this framework runs **Batched Matrix Multiplications (`torch.bmm`)** across all $N$ series concurrently.

### Algorithmic Loop Mechanics (for step $t$ in $T$):

1. **Prediction Step (State Transition):**
   $$P(S_t = k \mid Y_{t-1}) = \sum_j P(S_{t-1} = j \mid Y_{t-1}) \cdot P_{j, k}$$
   ```python
   # prev_xi: (N, K) -> unsqueezed: (N, 1, K)
   # transition_matrix: (N, K, K)
   xi_pred = torch.bmm(prev_xi.unsqueeze(1), transition_matrix).squeeze(1) # -> (N, K)
   ```

2. **Emission Step (Regime Conditional Density):**
   $$f(y_t \mid S_t = k) = \frac{1}{\sqrt{2\pi\sigma_k^2}} \exp\left(-\frac{(y_t - \mu_k)^2}{2\sigma_k^2}\right)$$
   ```python
   # y_t: (N, 1), mu: (N, K), variance: (N, K)
   eta = (1.0 / torch.sqrt(2.0 * torch.pi * variance)) * torch.exp(-((y_t - mu) ** 2) / (2.0 * variance))
   ```

3. **Update Step (Filtered Probabilities):**
   $$P(S_t = k \mid Y_t) = \frac{P(S_t = k \mid Y_{t-1}) \cdot f(y_t \mid S_t = k)}{\sum_m P(S_t = m \mid Y_{t-1}) \cdot f(y_t \mid S_t = m)}$$
   ```python
   joint_density = xi_pred * eta
   marginal_density = torch.sum(joint_density, dim=1, keepdim=True)
   current_xi = joint_density / (marginal_density + eps)
   ```

---

## 3. Solving the Regime Label-Switching Problem

Markov Regime-Switching models are symmetric with respect to state labels. Without ordering constraints, the states might emerge in arbitrary order (e.g., State 0 is Bear in time series A, but Bull in time series B).

To ensure **identifiability**, we apply a post-training **Parameter Permutation** to sort the states such that:
$$\mu_{i, 0} > \mu_{i, 1} > \dots > \mu_{i, K-1}$$

This establishes a uniform state classification across all assets:
- **State 0:** Bull Regime (Highest Mean Return)
- **State 1:** Neutral/Transition Regime
- **State K-1:** Bear Regime (Lowest Mean Return)

```python
# To enforce uniform state ordering:
model.sort_regimes()
```

---

## 4. Numerical Stability Constraints

To prevent numerical underflow/overflow during likelihood calculation:
- **Use Double Precision:** Always run likelihood computations with `torch.float64` (`torch.set_default_dtype(torch.float64)`).
- **Log-Likelihood Safeguards:** Pad divisions and log operations with a small epsilon (`eps = 1e-12`).

---

## 5. End-to-End Production Pattern

### 5.1 Training & Estimation

```python
import torch
from examples.mrs_model import MarkovRegimeSwitching, train_mrs_model

# Force float64 for absolute numerical stability
torch.set_default_dtype(torch.float64)

# Setup data: T steps, N series, K regimes
T, N, K = 500, 10, 2
y = torch.randn(T, N) # Dummy returns

# Instantiate and train
model = MarkovRegimeSwitching(num_series=N, num_states=K)
trained_model, loss_history = train_mrs_model(model, y, epochs=150, lr=0.05)

# Post-training: Sort states to guarantee Bull/Bear label alignment
trained_model.sort_regimes()

# Evaluate
trained_model.eval()
with torch.no_grad():
    mu, sigma, trans_mat = trained_model.get_constrained_params()
    total_nll, filtered_probabilities = trained_model(y)

# Print parameters for first series
print(f"Bull Mean: {mu[0, 0].item():.4f} | Bear Mean: {mu[0, 1].item():.4f}")
print(f"Transition Matrix:\n{trans_mat[0].numpy().round(4)}")
```

### 5.2 Transition Prediction

```python
from examples.mrs_model import predict_next_step

# Predict t+1 probabilities and expectations using latest state
last_state_prob = filtered_probabilities[-1] # shape (N, K)
next_probs, expected_values = predict_next_step(trained_model, last_state_prob)

for i in range(N):
    print(f"Asset {i} expected return: {expected_values[i].item():.5f}")
```

> [!NOTE]
> Fully runnable, production-grade implementations of the model, vectorized filter, and prediction APIs are hosted in `examples/mrs_model.py`.
