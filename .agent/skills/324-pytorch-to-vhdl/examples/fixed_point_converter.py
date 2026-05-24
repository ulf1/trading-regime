import torch
import torch.nn as nn
import numpy as np

def to_fixed(x: float, scale: int = 256, bits: int = 16) -> int:
    """
    Converts a float to a fixed-point signed integer.
    
    Args:
        x: Input float value.
        scale: Scaling factor (e.g., 2^8 for Q8.8).
        bits: Bit width of the integer.
        
    Returns:
        Integer representation of the fixed-point value.
    """
    # Scaling and rounding
    fixed_val = int(round(x * scale))
    
    # Range check for signed integer
    min_val = -(2 ** (bits - 1))
    max_val = (2 ** (bits - 1)) - 1
    
    if fixed_val < min_val:
        return min_val
    elif fixed_val > max_val:
        return max_val
    return fixed_val

def quantize_weights(model: nn.Module, scale: int = 256, bits: int = 16):
    """
    Quantizes weights of a PyTorch model and returns them as a dictionary of integers.
    """
    quantized_params = {}
    for name, param in model.named_parameters():
        param_np = param.detach().cpu().numpy()
        v_func = np.vectorize(lambda x: to_fixed(x, scale, bits))
        quantized_params[name] = v_func(param_np).tolist()
    return quantized_params

if __name__ == "__main__":
    # Example Usage:
    # 1.0 in Q8.8 is 256
    print(f"1.0 scaled (Q8.8): {to_fixed(1.0, 256)}")
    # -0.5 in Q8.8 is -128
    print(f"-0.5 scaled (Q8.8): {to_fixed(-0.5, 256)}")
    
    # Simple Model weight extraction
    class SimpleNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc1 = nn.Linear(8, 4)
            
    net = SimpleNet()
    q_weights = quantize_weights(net)
    print("Quantized Layer 'fc1.weight':")
    print(q_weights['fc1.weight'][0])
