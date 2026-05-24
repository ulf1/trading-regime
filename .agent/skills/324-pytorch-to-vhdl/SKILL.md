---
name: 324-pytorch-to-vhdl
description: High-performance orchestration for converting PyTorch models to synthesizable VHDL. Specializes in fixed-point quantization (Q8.8, Q1.15), layer-to-hardware mapping (MAC units, LUTs), and FPGA-optimized inference pipelines. Optimized for semantic discovery of hardware-accelerated machine learning and embedded AI deployment.
tags:
  - pytorch
  - vhdl
  - fpga
  - embedded-ai
  - quantization
  - dlnn
  - asic
capabilities:
  actions:
    - convert_pytorch_to_vhdl
    - validate_vhdl_inference
    - generate_fixed_point_weights
    - optimize_mac_pipelining
    - configure_vhdl_testbench
  file_extensions:
    - .py
    - .vhd
    - .vhdl
    - .sh
triggers:
  verbs:
    - convert
    - synthesize
    - quantize
    - simulate
    - deploy
  nouns:
    - VHDL
    - FPGA
    - Fixed-Point
    - HDL
    - MAC
    - Bit-Width
manifest:
  knowledge_base:
    - assets/layers.json
    - assets/manifest.json
  logic_examples:
    - examples/fixed_point_converter.py
    - examples/vhdl_model.vhd
    - examples/vhdl_testbench.vhd
    - examples/ghdl_simulation.sh
---

# PyTorch to VHDL Orchestration (Skill 324)

This skill enforces strict architectural patterns for hardware-level AI inference, focusing on **bit-accurate quantization** and **synthesizable RTL generation**.

## 1. High-Performance Conversion Workflow

1.  **Bit-Width Analysis**: Select quantization format (e.g., Q8.8) based on model range and hardware resources.
2.  **Weight Quantization**: Extract weights from `model.named_parameters()` and convert to integers using `examples/fixed_point_converter.py`.
3.  **RTL Mapping**: Map PyTorch layers (`nn.Linear`, `nn.ReLU`) to VHDL MAC units or comparators as defined in `assets/layers.json`.
4.  **Inference Pipeline**: Implement forward pass as a synchronous state machine (`clk`, `reset`) in `examples/vhdl_model.vhd`.
5.  **Verification**: Run cycle-accurate simulations using GHDL with `examples/vhdl_testbench.vhd` and verify bit-accurate matches with Python.

## 2. 🧩 High-Frequency Quantization Snippet

```python
# Convert float to fixed-point scaled integer
def to_fixed(x: float, scale: int = 256) -> int:
    return int(round(x * scale))

# Register weights as VHDL constants
weights = [to_fixed(w) for w in model.fc1.weight.data]
print(f"constant fc1_w : weight_array := ({', '.join(map(str, weights))});")
```

## 3. 🧪 VHDL Port Convention

Always use `IEEE.numeric_std` and clear synchronization signals.

```vhdl
entity model_top is
    port (
        clk    : in  std_logic;
        reset  : in  std_logic; -- Synchronous high-active reset
        start  : in  std_logic; -- Inference trigger
        input  : in  signed(15 downto 0); -- Q8.8 format
        output : out signed(15 downto 0);
        done   : out std_logic  -- Completion flag
    );
end entity;
```

> [!NOTE]
> Detailed layer-to-VHDL implementation strategies for Convolutional layers and LSTM blocks are documented in `assets/layers.json`. Comprehensive simulation scripts and end-to-end examples exceed 20 lines and are located in `examples/`.

## 4. Manifest & Knowledge Base
Refer to `assets/manifest.json` for detailed documentation on:
- Piecewise Linear Approximation for non-linear activations.
- Optimization strategies for Matrix-Matrix Multiplication on FPGAs.
- Pipelining for high-throughput inference throughput.
- Bit-accurate vs. Round-to-nearest overflow handling.
