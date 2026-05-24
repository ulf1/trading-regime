import numpy as np
import numpy.testing as npt
import pytest


def row_softmax(x: np.ndarray) -> np.ndarray:
    """Computes softmax along the last axis of a 2D array in a numerically stable way.

    Args:
        x: Input array of shape (N, D) or (D,)

    Returns:
        probabilities: Array of the same shape as input where elements sum to 1 along last axis.
    """
    if x.size == 0:
        return np.array([], dtype=x.dtype).reshape(x.shape)

    # Shift input to prevent overflow from exponentiation (numerical stability)
    max_val = np.max(x, axis=-1, keepdims=True)
    exp_x = np.exp(x - max_val)
    sum_exp = np.sum(exp_x, axis=-1, keepdims=True)

    return exp_x / sum_exp


# --- Pytest Test Suite ---


class TestRowSoftmax:
    """Robust test suite for verifying correctness, boundary behavior,

    and mathematical invariants of row_softmax.
    """

    @pytest.fixture
    def sample_matrix(self) -> np.ndarray:
        """Fixture representing a deterministic float32 input matrix."""
        return np.array(
            [[1.0, 2.0, 3.0], [10.0, 20.0, 30.0], [0.0, 0.0, 0.0]],
            dtype=np.float32,
        )

    def test_correct_values(self, sample_matrix):
        """Verify softmax probabilities for hand-verifiable configurations."""
        result = row_softmax(sample_matrix)

        # Expected value calculation for row 0:
        # e^1 / (e^1 + e^2 + e^3) ≈ 0.09003, e^2 / ... ≈ 0.2447, e^3 / ... ≈ 0.6652
        expected_row_0 = np.array([0.09003057, 0.24472848, 0.66524094], dtype=np.float32)

        # Float32 precision has ~6 decimal digits, so we use rtol=1e-5
        npt.assert_allclose(
            result[0],
            expected_row_0,
            rtol=1e-5,
            err_msg="Softmax value calculation is incorrect.",
        )

    def test_shapes_and_dtypes(self, sample_matrix):
        """Enforce strict preservation of dimensions, ranks, and exact numeric types."""
        result = row_softmax(sample_matrix)

        assert result.shape == sample_matrix.shape, "Output shape mismatch"
        assert result.ndim == sample_matrix.ndim, "Output dimension mismatch"
        assert result.dtype == sample_matrix.dtype, "Silent upcasting/type conversion detected!"

    @pytest.mark.parametrize("shape", [(10,), (5, 5), (2, 3, 4)])
    def test_parametrized_shapes(self, shape):
        """Enforce shape and dtype invariance across multiple array structures."""
        # Use isolated seed per test to keep randomness reproducible and independent
        rng = np.random.default_rng(seed=42)
        x = rng.standard_normal(shape, dtype=np.float32)

        result = row_softmax(x)
        assert result.shape == shape
        assert result.dtype == np.float32

    def test_mathematical_invariants(self):
        """Verify fundamental mathematical invariants: values sum to 1,

        monotonicity, and bounded output range [0, 1].
        """
        rng = np.random.default_rng(seed=123)
        x = rng.standard_normal((10, 5), dtype=np.float64)

        result = row_softmax(x)

        # Invariant 1: Output probabilities must sum to 1 along the last axis
        # float64 tolerance set explicitly to 1e-12
        npt.assert_allclose(
            np.sum(result, axis=-1),
            np.ones(10, dtype=np.float64),
            rtol=1e-12,
            err_msg="Softmax probabilities do not sum to 1.",
        )

        # Invariant 2: Values must lie strictly in the range [0.0, 1.0]
        assert np.all((result >= 0.0) & (result <= 1.0)), "Probabilities out of bounds."

        # Invariant 3: Monotonicity (larger inputs must yield larger probabilities)
        # If x_i > x_j, then softmax(x)_i > softmax(x)_j
        # Let's test this strictly on any row
        for i in range(10):
            sorted_indices_input = np.argsort(x[i])
            sorted_indices_output = np.argsort(result[i])
            npt.assert_array_equal(
                sorted_indices_input,
                sorted_indices_output,
                err_msg="Softmax violated monotonicity.",
            )

    def test_numerical_stability(self):
        """Verify numerically stable overflow protection (large scale inputs)."""
        # Exponents of 1000 would normally overflow float64 and produce NaNs
        large_input = np.array([[1000.0, 999.0, 998.0]], dtype=np.float64)

        # Softmax should subtract max_val first: [0.0, -1.0, -2.0]
        # Result: [e^0, e^-1, e^-2] / sum ≈ [0.668, 0.245, 0.090]
        result = row_softmax(large_input)

        assert not np.any(np.isnan(result)), "Softmax suffered from overflow NaN propagation."
        npt.assert_allclose(
            np.sum(result, axis=-1),
            np.ones(1, dtype=np.float64),
            rtol=1e-12,
        )

    def test_no_input_mutation(self, sample_matrix):
        """Ensure inputs are not modified in-place (no computational side-effects)."""
        input_backup = sample_matrix.copy()

        _ = row_softmax(sample_matrix)

        npt.assert_array_equal(
            sample_matrix,
            input_backup,
            err_msg="Target function mutated its input parameter!",
        )

    def test_non_contiguous_inputs(self, sample_matrix):
        """Verify computations execute identically on non-contiguous strided memory layouts."""
        # Transposing creates a column-major Fortran contiguous view
        transposed_input = sample_matrix.T
        assert not transposed_input.flags["C_CONTIGUOUS"], "Input is C-contiguous but F-contiguous was required."

        result_transposed = row_softmax(transposed_input)

        # Force contiguity to compare results
        contiguous_copy = np.ascontiguousarray(transposed_input)
        result_contiguous = row_softmax(contiguous_copy)

        npt.assert_allclose(
            result_transposed,
            result_contiguous,
            rtol=1e-5,
            err_msg="Computation failed on non-contiguous array strides.",
        )

    def test_empty_array(self):
        """Verify behavior with boundary elements (empty arrays)."""
        empty_input = np.array([], dtype=np.float32).reshape(0, 5)
        result = row_softmax(empty_input)

        assert result.shape == (0, 5), "Empty input dimensions were corrupted"
        assert result.size == 0
