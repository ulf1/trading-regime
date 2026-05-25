import pytest
import torch
from model import MarkovRegimeSwitching, train_mrs_model


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
    
    total_nll, filtered_probs = model(y)
    
    # Negative log likelihood should be a scalar tensor
    assert total_nll.ndim == 0
    assert total_nll.item() > 0
    
    # Filtered probabilities shape: (T, N, K)
    assert filtered_probs.shape == (T, N, K)
    assert filtered_probs.dtype == torch.float64
    
    # Elements of filtered probabilities should sum to 1.0 per step per series
    prob_sums = torch.sum(filtered_probs, dim=2)
    torch.testing.assert_close(prob_sums, torch.ones((T, N), dtype=torch.float64))

def test_parameter_sorting_logic():
    N, K = 3, 3
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    # Inject unsorted mu parameters
    with torch.no_grad():
        model.mu[0] = torch.tensor([1.5, 3.2, -0.5])  # Unsorted
        model.mu[1] = torch.tensor([-2.0, 5.0, 0.0])   # Unsorted
        model.mu[2] = torch.tensor([0.1, 0.2, 0.3])    # Unsorted
        
        # Inject standard transitions
        model.raw_trans_mat.fill_(0.0)
    
    # Apply parameter sorting
    model.sort_regimes()
    
    mu_sorted, _, _ = model.get_constrained_params()
    
    # Check that mu for every series is strictly sorted in descending order: mu_0 > mu_1 > mu_2
    for i in range(N):
        assert mu_sorted[i, 0] > mu_sorted[i, 1]
        assert mu_sorted[i, 1] > mu_sorted[i, 2]

def test_gradient_flow():
    T, N, K = 50, 2, 3
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    y = torch.randn(T, N)
    
    # Verify autograd graphs are connected properly
    total_nll, _ = model(y)
    total_nll.backward()
    
    # Check model parameters received non-zero gradients
    assert model.mu.grad is not None
    assert not torch.all(model.mu.grad == 0.0)
    
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
    torch.testing.assert_close(model1.mu, model2.mu)
    torch.testing.assert_close(model1.raw_sigma, model2.raw_sigma)
    torch.testing.assert_close(model1.raw_trans_mat, model2.raw_trans_mat)
