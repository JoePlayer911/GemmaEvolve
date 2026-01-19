#!/bin/bash
# Visualize Verilog simulation using GTKWave

INPUT_FILE=${1:-"examples/verilog_optimization/openevolve_output/best/best_program.v"}
TESTBENCH="examples/verilog_optimization/testbench.v"
OUTPUT_EXEC="sim_vis.out"
VCD_FILE="waveform.vcd"

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found."
    echo "Usage: ./visualize_verilog.sh [path_to_verilog_file]"
    exit 1
fi

echo "Compiling $INPUT_FILE with visualization enabled..."

# Compile with DUMP_WAVEFORM definition
iverilog -D DUMP_WAVEFORM -o "$OUTPUT_EXEC" "$INPUT_FILE" "$TESTBENCH"

if [ $? -ne 0 ]; then
    echo "Compilation failed."
    exit 1
fi

echo "Running simulation..."
vvp "$OUTPUT_EXEC"

if [ -f "$VCD_FILE" ]; then
    echo "Simulation complete. Opening GTKWave..."
    gtkwave "$VCD_FILE" &
else
    echo "Error: VCD file was not generated."
    exit 1
fi
