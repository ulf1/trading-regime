import pytest
import torch
from model import MarkovRegimeSwitching, train_mrs_model, occupancy_prior


# Force float64 for absolute numerical stability as required by the model
torch.set_default_dtype(torch.float64)

def test_model_initialization_and_constraints():
    N, K = 5, 3
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    assert model.num_series == N
    assert model.num_states == K
    
    # Check constrained parameters
    mu, sigma, transition_matrix = model.get_constrained_params()
    
    assert mu.shape == (N, K)
    assert sigma.shape == (N, K)
    assert transition_matrix.shape == (N, K, K)
    
    # Sigma must be strictly positive (> 0)
    assert torch.all(sigma > 0)
    
    # Transition matrix columns (rows inside transition) must sum to 1.0 (dim=2)
    row_sums = torch.sum(transition_matrix, dim=2)
    torch.testing.assert_close(row_sums, torch.ones((N, K), dtype=torch.float64))

def test_model_forward_shape_and_nll():
    T, N, K = 100, 4, 3
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    # Generate dummy data
    y = torch.randn(T, N)
    
    total_nll, filtered_probs, individual_nlls = model(y)
    
    # Negative log likelihood should be a scalar tensor
    assert total_nll.ndim == 0
    assert total_nll.item() > 0
    
    # Filtered probabilities shape: (T, N, K)
    assert filtered_probs.shape == (T, N, K)
    
    # Individual NLLs shape: (N,)
    assert individual_nlls.shape == (N,)

    assert filtered_probs.dtype == torch.float64
    
    # Elements of filtered probabilities should sum to 1.0 per step per series
    prob_sums = torch.sum(filtered_probs, dim=2)
    torch.testing.assert_close(prob_sums, torch.ones((T, N), dtype=torch.float64))

def test_parameter_ordering_constraint():
    N, K = 3, 3
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    # Inject various raw_mu values (unconstrained alpha, beta, gamma)
    with torch.no_grad():
        model.raw_mu[0] = torch.tensor([1.5, 3.2, -0.5])
        model.raw_mu[1] = torch.tensor([-2.0, 5.0, 0.0])
        model.raw_mu[2] = torch.tensor([0.1, 0.2, 0.3])
    
    mu_sorted, _, _ = model.get_constrained_params()
    
    # Check that mu for every series is strictly sorted: mu_bull (0) >= mu_neutral (1) >= mu_bear (2)
    for i in range(N):
        assert mu_sorted[i, 0] >= mu_sorted[i, 1]
        assert mu_sorted[i, 1] >= mu_sorted[i, 2]

def test_gradient_flow():
    T, N, K = 50, 2, 3
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    y = torch.randn(T, N)
    
    # Verify autograd graphs are connected properly
    total_nll, _, _ = model(y)

    total_nll.backward()
    
    # Check model parameters received non-zero gradients
    assert model.raw_mu.grad is not None
    assert not torch.all(model.raw_mu.grad == 0.0)
    
    assert model.raw_sigma.grad is not None
    assert not torch.all(model.raw_sigma.grad == 0.0)
    
    assert model.raw_trans_mat.grad is not None
    assert not torch.all(model.raw_trans_mat.grad == 0.0)

def test_model_determinism():
    T, N, K = 50, 3, 3
    y = torch.randn(T, N)
    
    # Run 1
    torch.manual_seed(42)
    model1 = MarkovRegimeSwitching(num_series=N, num_states=K)
    model1, losses1 = train_mrs_model(model1, y, epochs=10, lr=0.01)
    
    # Run 2
    torch.manual_seed(42)
    model2 = MarkovRegimeSwitching(num_series=N, num_states=K)
    model2, losses2 = train_mrs_model(model2, y, epochs=10, lr=0.01)
    
    # Check loss values are identical
    assert losses1 == losses2
    
    # Check model parameters are identical
    torch.testing.assert_close(model1.raw_mu, model2.raw_mu)
    torch.testing.assert_close(model1.raw_sigma, model2.raw_sigma)
    torch.testing.assert_close(model1.raw_trans_mat, model2.raw_trans_mat)

def test_occupancy_prior():
    T, N, K = 100, 5, 3
    
    # Create perfect match probabilities
    probs = torch.zeros(T, N, K, dtype=torch.float64)
    probs[:, :, 0] = 0.3
    probs[:, :, 1] = 0.4
    probs[:, :, 2] = 0.3
    
    # Penalty should be exactly 0
    penalty = occupancy_prior(probs, target=(0.3, 0.4, 0.3), lam=50.0)
    torch.testing.assert_close(penalty, torch.tensor(0.0, dtype=torch.float64))
    
    # Create deviating probabilities
    probs_bad = torch.zeros(T, N, K, dtype=torch.float64)
    probs_bad[:, :, 0] = 0.5
    probs_bad[:, :, 1] = 0.5
    probs_bad[:, :, 2] = 0.0
    
    penalty_bad = occupancy_prior(probs_bad, target=(0.3, 0.4, 0.3), lam=50.0)
    
    # Mean over 0 gives (0.5, 0.5, 0.0) for each of the N series.
    # Deviation from target: (0.2, 0.1, -0.3)
    # Squared dev: (0.04, 0.01, 0.09) -> sum per series = 0.14
    # Mean over N series and K states: 0.14 / K = 0.04666...
    # Lam = 50.0 -> penalty = 50.0 * 0.14 / 3 = 2.3333...
    
    expected_penalty = 50.0 * (0.2**2 + 0.1**2 + 0.3**2) / K
    torch.testing.assert_close(penalty_bad, torch.tensor(expected_penalty, dtype=torch.float64))
