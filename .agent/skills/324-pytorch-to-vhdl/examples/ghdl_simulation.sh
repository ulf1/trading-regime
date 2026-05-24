#!/bin/bash

# GHDL Simulation Script for PyTorch to VHDL Models
# Ensure GHDL is installed (sudo apt install ghdl)

# 1. Analyze (Syntax Check)
ghdl -a vhdl_model.vhd vhdl_testbench.vhd

# 2. Elaborate (Build Entity)
ghdl -e vhdl_testbench

# 3. Register and Run
ghdl -r vhdl_testbench --vcd=wave.vcd

# 4. View results (Optional: Requires GTKWave)
# gtkwave wave.vcd
echo "Simulation Complete. Results in wave.vcd"
