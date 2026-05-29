import logging
import torch
import torch.nn as nn
from typing import Tuple, List

logger = logging.getLogger(__name__)

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
        # Raw mu parameterized for ordering constraint (alpha, beta, gamma): shape (N, K)
        self.raw_mu = nn.Parameter(torch.tensor([[-0.0183, -4.0, -4.0] for _ in range(num_series)], dtype=torch.float64))
        
        # Log of standard deviations to ensure variance is strictly positive: shape (N, K)
        self.raw_sigma = nn.Parameter(torch.zeros(num_series, num_states, dtype=torch.float64))
        
        # Unconstrained logits for transition probability matrix: shape (N, K, K)
        # Raw value raw_trans_mat[i, j, k] corresponds to transition from state j to state k
        self.raw_trans_mat = nn.Parameter(torch.tensor([[
            [2., -2, -2],
            [-2, 2., -2],
            [-2, -2, 2.]
        ] for _ in range(num_series)], dtype=torch.float64))
        
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
        - mu: Enforces order mu_bear <= mu_neutral <= mu_bull
        
        Returns:
            mu: Means, shape (N, K)
            sigma: Standard deviations, shape (N, K)
            transition_matrix: Valid probability transition matrix, shape (N, K, K)
        """
        sigma = torch.exp(self.raw_sigma)
        transition_matrix = torch.softmax(self.raw_trans_mat, dim=2)
        
        alpha = self.raw_mu[:, 0]
        beta = self.raw_mu[:, 1]
        gamma = self.raw_mu[:, 2]
        
        mu_bear = alpha
        mu_neutral = alpha + torch.exp(beta)
        mu_bull = alpha + torch.exp(beta) + torch.exp(gamma)
        
        mu = torch.stack([mu_bull, mu_neutral, mu_bear], dim=1)
        
        return mu, sigma, transition_matrix

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
        total_nll = individual_nlls.mean()
        
        return total_nll, filtered_probs, individual_nlls



def occupancy_prior(
    state_probs: torch.Tensor,
    target: Tuple[float, float, float] = (0.3, 0.4, 0.3),
    lam: float = 50.0
) -> torch.Tensor:
    """
    Calculates a Bayesian-style occupancy prior penalty.
    Penalizes the deviation of the mean state probabilities from a target distribution.
    """
    occ = state_probs.mean(0)
    
    target_tensor = torch.tensor(
        target,
        device=occ.device,
        dtype=occ.dtype
    )
    
    return lam * ((occ - target_tensor)**2).mean()


def transition_persistence_penalty(
    model: MarkovRegimeSwitching,
    lam: float = 100.0   # the value must be relative to NLL (4-5 digits)
) -> torch.Tensor:
    """
    Calculates a penalty to encourage high diagonal entries in the transition matrix,
    representing persistence (regimes tend to stay in the same state).

    This matches:
        [
        \text{loss} = \frac{1}{n}\sum_i \max(0, 0.8 - p_{ii})^2
        ]
    """
    _, _, trans_mat = model.get_constrained_params()
    
    # Sum of diagonal elements for each series
    persistence = torch.diagonal(trans_mat, dim1=1, dim2=2)
    
    # Penalty if diagonal is less than 0.8 (i.e. proba of at least 5 days staying in the regime)
    return lam * (torch.clamp(0.8 - persistence, min=0) ** 2).mean()


def regime_volatility_penalty(
    model: MarkovRegimeSwitching,
    lam: float = 50.0
) -> torch.Tensor:
    """
    Penalizes the difference in volatility between regimes.
    - bull regime is around 0.75x of neutral regime
    - bear regime is around 2.0x of neutral regime
    """
    _, sigma, _ = model.get_constrained_params()
    return lam * (
        (sigma[:, 0] - 0.75 * sigma[:, 1]) ** 2 + (sigma[:, 2] - 2.0 * sigma[:, 1]) ** 2
    ).mean()


def train_mrs_model(
    model: MarkovRegimeSwitching, 
    y: torch.Tensor, 
    epochs: int = 100, 
    lr: float = 0.05,
) -> Tuple[MarkovRegimeSwitching, List[float]]:
    """
    Standard training pipeline for the Markov Regime-Switching model using the Adam optimizer.
    
    Args:
        model: An instantiated MarkovRegimeSwitching module.
        y: Observation tensor of shape (T, N).
        epochs: Number of training iterations.
        lr: Learning rate for the optimizer.
        lam: Lambda scaling factor for the occupancy prior penalty.
        target_occ: Target state occupancies.
        
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
        nll, filtered_probs, _ = model(y)

        # Penalties
        penalty_occ = occupancy_prior(filtered_probs)
        penalty_pers = transition_persistence_penalty(model)
        penalty_vol = regime_volatility_penalty(model)
        
        # loss function
        loss = nll + penalty_occ + penalty_pers + penalty_vol
        
        # Backpropagation
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
        
        if epoch % 20 == 0 or epoch == epochs - 1:
            logger.info(
                f"Epoch {epoch:03d}/{epochs:03d} | Loss: {loss.item():.4f} | "
                f"NLL: {nll.item():.4f} | Occ Penalty: {penalty_occ.item():.4f} | "
                f"Pers Penalty: {penalty_pers.item():.4f} | Vol Penalty: {penalty_vol.item():.4f}"
            )
        
    return model, losses
