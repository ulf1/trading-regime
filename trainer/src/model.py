import torch
import torch.nn as nn
from typing import Tuple, List

class MarkovRegimeSwitching(nn.Module):
    """
    Batched Markov Regime-Switching (MRS) Model for multiple independent time series.
    
    This implementation leverages parallel batched tensor operations and PyTorch's 
    autograd framework to train multiple time series concurrently, bypassing the 
    need for nested loops or custom Expectation-Maximization (EM) steps.
    
    Tensor Shapes:
        N: Number of independent time series
        K: Number of states/regimes
        T: Number of time steps
    """
    def __init__(self, num_series: int, num_states: int = 3):
        super().__init__()
        self.num_series = num_series
        self.num_states = num_states
        
        # Unconstrained parameters optimized directly via autograd.
        # Mean of each state for each time series: shape (N, K)
        self.mu = nn.Parameter(torch.randn(num_series, num_states))
        
        # Log of standard deviations to ensure variance is strictly positive: shape (N, K)
        self.raw_sigma = nn.Parameter(torch.zeros(num_series, num_states))
        
        # Unconstrained logits for transition probability matrix: shape (N, K, K)
        # Raw value raw_trans_mat[i, j, k] corresponds to transition from state j to state k
        self.raw_trans_mat = nn.Parameter(torch.zeros(num_series, num_states, num_states))
        
        # Initial state probabilities: shape (N, K). Defaults to a uniform distribution.
        self.register_buffer(
            'initial_prob', 
            torch.ones(num_series, num_states) / num_states
        )

    def get_constrained_params(self) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Applies reparameterization constraints to raw parameters:
        - sigma = exp(raw_sigma) -> Guarantees strictly positive standard deviations.
        - transition_matrix = softmax(raw_trans_mat, dim=2) -> Guarantees row-stochastic matrices.
        
        Returns:
            mu: Means, shape (N, K)
            sigma: Standard deviations, shape (N, K)
            transition_matrix: Valid probability transition matrix, shape (N, K, K)
        """
        sigma = torch.exp(self.raw_sigma)
        transition_matrix = torch.softmax(self.raw_trans_mat, dim=2)
        return self.mu, sigma, transition_matrix

    def forward(self, y: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Runs the batched Hamilton Filter to compute the negative log-likelihood.
        
        Args:
            y: Observation tensor of shape (T, N) where T is time steps and N is number of series.
               Note: Best trained using torch.float64 for numerical stability.
            
        Returns:
            total_nll: Scalar tensor representing the total Negative Log-Likelihood across all series.
            filtered_probs: Tensor of shape (T, N, K) containing P(S_t = k | Y_t).
        """
        T, N = y.shape
        assert N == self.num_series, f"Input has {N} series but model is initialized for {self.num_series} series."
        
        mu, sigma, transition_matrix = self.get_constrained_params()
        
        eps = 1e-12
        variance = (sigma ** 2) + eps
        
        log_likelihood = torch.zeros(N, dtype=y.dtype, device=y.device)
        filtered_probs = torch.zeros((T, N, self.num_states), dtype=y.dtype, device=y.device)
        
        prev_xi = self.initial_prob
        
        for t in range(T):
            # 1. Prediction Step: P(S_t | Y_{t-1}) = P(S_{t-1} | Y_{t-1}) * P_transition
            # prev_xi: (N, K) -> unsqueezed: (N, 1, K)
            # transition_matrix: (N, K, K)
            # xi_pred: (N, 1, K) -> squeezed: (N, K)
            xi_pred = torch.bmm(prev_xi.unsqueeze(1), transition_matrix).squeeze(1)
            
            # 2. Emission Step: Density calculation eta_t = f(y_t | S_t)
            # y_t: (N, 1)
            y_t = y[t].unsqueeze(1)
            eta = (1.0 / torch.sqrt(2.0 * torch.pi * variance)) * \
                  torch.exp(-((y_t - mu) ** 2) / (2.0 * variance))
            
            # 3. Update Step: P(S_t | Y_t)
            joint_density = xi_pred * eta
            marginal_density = torch.sum(joint_density, dim=1, keepdim=True)
            
            current_xi = joint_density / (marginal_density + eps)
            
            # Store values
            filtered_probs[t] = current_xi
            log_likelihood = log_likelihood + torch.log(marginal_density.squeeze(1) + eps)
            prev_xi = current_xi
            
        # Individual NLL per series (shape: N) and overall total NLL (scalar)
        individual_nlls = -log_likelihood
        total_nll = individual_nlls.sum()
        
        return total_nll, filtered_probs, individual_nlls


    @torch.no_grad()
    def sort_regimes(self) -> None:
        """
        Sorts the regimes/states for each independent time series in descending order 
        of their estimated means (mu). This resolves the label-switching problem, 
        ensuring that:
        - State 0 Consistently represents the "high-mean/bull" regime.
        - State 1 represents the "neutral/intermediate" regime.
        - State 2 represents the "low-mean/bear" regime.
        """
        # Find descending indices based on mu: shape (N, K)
        sort_indices = torch.argsort(self.mu, dim=1, descending=True)
        
        # Sort mu and raw_sigma using gather
        self.mu.data = torch.gather(self.mu.data, 1, sort_indices)
        self.raw_sigma.data = torch.gather(self.raw_sigma.data, 1, sort_indices)
        
        # Sort the 3D transition probability logits: shape (N, K, K)
        # We must permute both rows (state t-1) and columns (state t) for each series i
        K = self.num_states
        
        # 1. Permute rows (dim 1)
        idx_rows = sort_indices.unsqueeze(2).expand(-1, -1, K)
        temp = torch.gather(self.raw_trans_mat.data, 1, idx_rows)
        
        # 2. Permute columns (dim 2)
        idx_cols = sort_indices.unsqueeze(1).expand(-1, K, -1)
        self.raw_trans_mat.data = torch.gather(temp, 2, idx_cols)


def train_mrs_model(
    model: MarkovRegimeSwitching, 
    y: torch.Tensor, 
    epochs: int = 150, 
    lr: float = 0.05
) -> Tuple[MarkovRegimeSwitching, List[float]]:
    """
    Standard training pipeline for the Markov Regime-Switching model using the Adam optimizer.
    
    Args:
        model: An instantiated MarkovRegimeSwitching module.
        y: Observation tensor of shape (T, N).
        epochs: Number of training iterations.
        lr: Learning rate for the optimizer.
        
    Returns:
        model: The trained model (in-place modification).
        losses: List of negative log-likelihood values over epochs.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    losses = []
    
    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad(set_to_none=True)
        
        # Forward pass
        loss, _, _ = model(y)

        
        # Backpropagation
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
        
    return model, losses
