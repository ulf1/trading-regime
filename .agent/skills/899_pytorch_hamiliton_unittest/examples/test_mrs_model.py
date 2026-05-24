import sys
import os
import torch
import pytest

# Ensure the sibling skill directory is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_skills_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(os.path.join(parent_skills_dir, "899_pytorch_hamiliton"))

from examples.mrs_model import MarkovRegimeSwitching, train_mrs_model, predict_next_step

@pytest.fixture(autouse=True)
def setup_precision():
    """Sets standard high precision float64 for all tests."""
    torch.set_default_dtype(torch.float64)
    yield


def test_parameter_constraints_initialization():
    """
    Verifies that the raw parameters are correctly initialized and constraint mappings
    (exponential for standard deviation, softmax for transition matrix) produce valid domains.
    """
    num_series = 3
    num_states = 2
    model = MarkovRegimeSwitching(num_series=num_series, num_states=num_states)
    
    # Assert initial parameters match dimensions
    assert model.mu.shape == (num_series, num_states)
    assert model.raw_sigma.shape == (num_series, num_states)
    assert model.raw_trans_mat.shape == (num_series, num_states, num_states)
    
    # Assert uniform initial probabilities
    assert torch.allclose(model.initial_prob, torch.ones(num_series, num_states) / num_states)
    
    # Extract constraints
    mu, sigma, trans_mat = model.get_constrained_params()
    
    # Sigma must be strictly positive
    assert torch.all(sigma > 0), "Standard deviations must be strictly positive"
    
    # Transition probability rows must sum to 1.0 (probabilities)
    assert torch.allclose(trans_mat.sum(dim=2), torch.ones(num_series, num_states)), \
        "Transition matrix rows must sum to 1.0"
    assert torch.all(trans_mat >= 0), "Transition probabilities must be non-negative"


def test_hamilton_filter_forward_pass():
    """
    Validates that a forward pass computes expected shapes, NLL scalar reductions,
    and valid filtered probability assignments that sum to 1.0 at every time step.
    """
    T, N, K = 50, 4, 3
    y = torch.randn(T, N)
    
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    # Forward Pass
    nll, filtered_probs = model(y)
    
    # NLL check
    assert isinstance(nll, torch.Tensor)
    assert nll.dim() == 0, "Negative log-likelihood must be a scalar tensor"
    assert not torch.isnan(nll), "Negative log-likelihood must not be NaN"
    
    # Filtered probabilities check
    assert filtered_probs.shape == (T, N, K), "Filtered probabilities must match dimensions (T, N, K)"
    assert torch.all(filtered_probs >= 0), "Filtered probabilities must be non-negative"
    assert torch.allclose(filtered_probs.sum(dim=2), torch.ones(T, N)), \
        "Filtered probabilities must sum to 1.0 at every time step for all series"


def test_regime_identifiability_sorting():
    """
    Validates that sort_regimes() correctly orders states by mean in descending order,
    and correctly permutes other parameters (sigmas and transition matrices) accordingly.
    """
    N, K = 2, 3
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    # Manually configure unsorted means to force sorting permutation
    # Series 0: state 1 has highest, state 2 middle, state 0 lowest
    # Series 1: state 2 has highest, state 0 middle, state 1 lowest
    model.mu.data = torch.tensor([
        [1.0, 5.0, 3.0],
        [2.0, -1.0, 4.0]
    ])
    
    # Manually configure raw_sigma and raw_trans_mat to trace them after permutation
    model.raw_sigma.data = torch.tensor([
        [10.0, 20.0, 30.0],
        [40.0, 50.0, 60.0]
    ])
    
    # transition logit shape: (N, K, K)
    # raw_trans_mat[i, j, k] corresponds to transition from j to k.
    # We populate the matrix with distinct values to verify permutations
    model.raw_trans_mat.data = torch.tensor([
        [[0.0, 1.0, 2.0], [3.0, 4.0, 5.0], [6.0, 7.0, 8.0]],
        [[10.0, 11.0, 12.0], [13.0, 14.0, 15.0], [16.0, 17.0, 18.0]]
    ])
    
    # Run Sorting
    model.sort_regimes()
    
    # Check Means: Must be in strictly descending order
    sorted_mu = model.mu.detach().numpy()
    assert sorted_mu[0, 0] == 5.0 and sorted_mu[0, 1] == 3.0 and sorted_mu[0, 2] == 1.0
    assert sorted_mu[1, 0] == 4.0 and sorted_mu[1, 1] == 2.0 and sorted_mu[1, 2] == -1.0
    
    # Check Sigmas: Must have permuted identically to mu
    # Series 0 sort permutation order was: State 1 -> State 2 -> State 0
    # Expected sorted sigmas for Series 0: 20.0, 30.0, 10.0
    sorted_sigma = model.raw_sigma.detach().numpy()
    assert sorted_sigma[0, 0] == 20.0 and sorted_sigma[0, 1] == 30.0 and sorted_sigma[0, 2] == 10.0
    
    # Series 1 sort permutation order was: State 2 -> State 0 -> State 1
    # Expected sorted sigmas for Series 1: 60.0, 40.0, 50.0
    assert sorted_sigma[1, 0] == 60.0 and sorted_sigma[1, 1] == 40.0 and sorted_sigma[1, 2] == 50.0
    
    # Check raw_trans_mat permutation:
    # Row and Column indices must both follow the same permutation mapping.
    # For Series 0: perm = [1, 2, 0]
    # Original raw_trans_mat[0]:
    # [[0, 1, 2],
    #  [3, 4, 5],
    #  [6, 7, 8]]
    # Permuting rows (dim 1) and cols (dim 2) by [1, 2, 0]:
    # new[j, k] = old[perm[j], perm[k]]
    # j=0, k=0 -> old[1, 1] = 4
    # j=0, k=1 -> old[1, 2] = 5
    # j=0, k=2 -> old[1, 0] = 3
    # j=1, k=0 -> old[2, 1] = 7
    # j=1, k=1 -> old[2, 2] = 8
    # j=1, k=2 -> old[2, 0] = 6
    # j=2, k=0 -> old[0, 1] = 1
    # j=2, k=1 -> old[0, 2] = 2
    # j=2, k=2 -> old[0, 0] = 0
    # Expected new trans:
    # [[4, 5, 3],
    #  [7, 8, 6],
    #  [1, 2, 0]]
    sorted_trans = model.raw_trans_mat.detach().numpy()
    expected_trans_0 = [[4.0, 5.0, 3.0], [7.0, 8.0, 6.0], [1.0, 2.0, 0.0]]
    assert (sorted_trans[0] == expected_trans_0).all(), f"Transition matrix permutation mismatch on Series 0: {sorted_trans[0]}"


def test_prediction_step():
    """
    Verifies that predict_next_step computes proper transition forecasting
    producing correct shapes and state probabilities that sum to 1.0.
    """
    N, K = 3, 2
    model = MarkovRegimeSwitching(num_series=N, num_states=K)
    
    # Filtered probabilities for last step
    last_prob = torch.tensor([
        [0.8, 0.2],
        [0.1, 0.9],
        [0.5, 0.5]
    ])
    
    next_state_prob, expected_y = predict_next_step(model, last_prob)
    
    # Assert shapes
    assert next_state_prob.shape == (N, K)
    assert expected_y.shape == (N,)
    
    # Probabilities must sum to 1.0
    assert torch.allclose(next_state_prob.sum(dim=1), torch.ones(N)), \
        "Predicted probabilities must sum to 1.0"
    assert torch.all(next_state_prob >= 0)


def test_input_validation_errors():
    """
    Validates model raises assertions under incorrect batch dimension inputs.
    """
    model = MarkovRegimeSwitching(num_series=5, num_states=2)
    y_invalid = torch.randn(100, 3) # Model expects 5 series, input has 3
    
    with pytest.raises(AssertionError):
        model(y_invalid)
