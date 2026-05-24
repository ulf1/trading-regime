import numpy as np
import numpy.typing as npt
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, Field


class ComputationConfig(BaseModel):
    """Pydantic configuration for high-performance NumPy execution."""

    num_samples: int = Field(default=1000, gt=0)
    feature_dim: int = Field(default=64, gt=0)
    top_k: int = Field(default=5, gt=0)
    num_threads: int = Field(default=4, gt=0)
    seed: int = Field(default=42, ge=0)


def prepare_inference_matrix(
    raw_features: list[float] | list[list[float]]
) -> npt.NDArray[np.float64]:
    """Standardizes feature inputs into a validated 2D float64 NumPy array.

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


def label_feedback_vector(
    predictions: np.ndarray, feedbacks: np.ndarray
) -> np.ndarray:
    """Transforms generic user feedback vectors into robust true training labels.

    - feedback == 1 (thumbs up) -> use predicted class
    - feedback == 0 (thumbs down) -> label is masked or needs manual true input
    """
    # 1 indicates Thumbs Up, 0 indicates Thumbs Down, -1 indicates No Feedback
    return np.where(feedbacks == 1, predictions, -1)


def compute_pairwise_distances(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Compute pairwise Euclidean distances between two sets of vectors using broadcasting.

    This implements the memory-efficient outer-product broadcast trick without copying.

    Args:
        x: Array of shape (N, D)
        y: Array of shape (M, D)

    Returns:
        distances: Array of shape (N, M) containing Euclidean distances.
    """
    # Explicit shape validation
    if x.ndim != 2 or y.ndim != 2:
        raise ValueError(
            f"Inputs must be 2D arrays, got ndim={x.ndim} and {y.ndim}"
        )
    if x.shape[1] != y.shape[1]:
        raise ValueError(
            f"Feature dimensions must match, got {x.shape[1]} and {y.shape[1]}"
        )

    # Use broadcasting: x[:, np.newaxis, :] is (N, 1, D)
    # y[np.newaxis, :, :] is (1, M, D)
    # Difference has shape (N, M, D)
    diff = x[:, np.newaxis, :] - y[np.newaxis, :, :]

    # Sum of squares along the feature axis (axis=2)
    # Using keepdims=False since we want to collapse it to (N, M)
    return np.sqrt(np.sum(diff**2, axis=2))


def fast_top_k_indices(distances: np.ndarray, k: int) -> np.ndarray:
    """Find indices of the top-k smallest distances for each query vector.

    Utilizes np.argpartition to achieve O(N) complexity instead of O(N log N) from argsort.

    Args:
        distances: Array of shape (N, M)
        k: Number of nearest neighbors to retrieve

    Returns:
        top_k_idx: Array of shape (N, k) containing indices of the k smallest elements (unsorted).
    """
    if k > distances.shape[1]:
        raise ValueError(
            f"k={k} cannot be larger than the number of columns ({distances.shape[1]})"
        )

    # np.argpartition partitions elements such that the k-th element is at its sorted position,
    # and all smaller elements are placed before it. We slice the first k elements.
    partitioned = np.argpartition(distances, kth=k, axis=1)
    return partitioned[:, :k]


def process_chunk_gil_free(chunk: np.ndarray) -> np.ndarray:
    """Applies a 1D FFT to each row in the chunk.

    NumPy releases the Python GIL during heavy C-level calculations (like FFT),
    allowing parallel thread execution.

    Args:
        chunk: Array of shape (C, D)

    Returns:
        fft_result: Real power spectrum of shape (C, D // 2 + 1)
    """
    # np.fft.rfft performs a 1D FFT on real input, releasing the GIL
    fft_vals = np.fft.rfft(chunk, axis=1)
    return np.abs(fft_vals)


def parallel_spectral_analysis(data: np.ndarray, num_threads: int) -> np.ndarray:
    """Analyze a large dataset concurrently using multiple threads.

    NumPy releases the GIL for FFT computations, allowing ThreadPoolExecutor
    to achieve genuine parallel CPU scaling.

    Args:
        data: Array of shape (N, D)
        num_threads: Number of parallel worker threads

    Returns:
        spectral_power: Concat spectral power array of shape (N, D // 2 + 1)
    """
    # Ensure memory is contiguous for optimal cache and vectorization performance
    data_contiguous = np.ascontiguousarray(data, dtype=np.float32)

    # Split dataset into chunks along the row axis
    chunks = np.array_split(data_contiguous, num_threads, axis=0)

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        results = list(executor.map(process_chunk_gil_free, chunks))

    # Recombine chunks into a single array
    return np.concatenate(results, axis=0)


def main():
    # Instantiate pydantic configuration
    config = ComputationConfig()

    # Reproducible random number generation using the modern Generator API
    rng = np.random.default_rng(seed=config.seed)

    print(
        f"Generating synthetic datasets (Float32 for optimal memory/speed)..."
    )
    # Create float32 arrays explicitly to prevent silent upcasting to float64
    x = rng.standard_normal(
        (config.num_samples, config.feature_dim), dtype=np.float32
    )
    y = rng.standard_normal(
        (config.num_samples // 2, config.feature_dim), dtype=np.float32
    )

    print(f"Computing pairwise Euclidean distances (broadcasting)...")
    distances = compute_pairwise_distances(x, y)
    print(f"Distance array shape: {distances.shape} (Expected: ({x.shape[0]}, {y.shape[0]}))")

    print(f"Finding top-{config.top_k} nearest neighbors via O(N) argpartition...")
    top_k_indices = fast_top_k_indices(distances, config.top_k)
    print(f"Indices array shape: {top_k_indices.shape}")

    print(f"Performing concurrent, GIL-free spectral analysis...")
    spectral_power = parallel_spectral_analysis(x, config.num_threads)
    print(f"Spectral power shape: {spectral_power.shape}")

    # Verify input arrays were not mutated (numerical hygiene check)
    assert x.shape == (config.num_samples, config.feature_dim)
    assert y.shape == (config.num_samples // 2, config.feature_dim)

    # Verify new shape-safe feature preparation and label mapping features
    print("Verifying shape-safe feature preparation...")
    raw_1d = [1.5, 2.5, 3.5]
    prepared_2d = prepare_inference_matrix(raw_1d)
    assert prepared_2d.shape == (1, 3)
    assert prepared_2d.dtype == np.float64

    print("Verifying vectorized feature engineering label mapping...")
    preds = np.array([1, 2, 0, 1])
    feedbacks = np.array([1, 0, 1, 0])
    mapped_labels = label_feedback_vector(preds, feedbacks)
    assert np.array_equal(mapped_labels, [1, -1, 0, -1])

    print("Verification complete: All new and existing features validated successfully!")


if __name__ == "__main__":
    main()
