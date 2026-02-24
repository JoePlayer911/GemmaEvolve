# GemmaEvolve Setup Guide

This guide covers how to set up and run OpenEvolve with the local Gemma model on a new device.

## Prerequisites

- **Python 3.8+** (recommended: Python 3.10)
- **Git** for cloning the repository
- **~10GB free disk space** (for model file and dependencies)

## Step 1: Clone the Repository

```bash
git clone https://github.com/JoePlayer911/GemmaEvolve.git
cd GemmaEvolve
```

## Step 2: Download the Gemma Model (GGUF)

The Gemma model file is **not included** in the repository due to its large size (~2.5GB). You need to download it separately:

### Option A: If you have the model file
Copy your `gemma-3-4b-it-UD-Q4_K_XL.gguf` file to the root directory of the project:
```
GemmaEvolve/
├── gemma-3-4b-it-UD-Q4_K_XL.gguf  ← Place it here
├── openevolve/
├── examples/
└── ...
```

### Option B: Download from Hugging Face
Visit [Hugging Face Model Hub](https://huggingface.co/) and search for "gemma-3-4b-it GGUF" or use a quantized version compatible with llama-cpp-python.

Example download command (if available):
```bash
# Replace with actual model URL
wget https://huggingface.co/.../gemma-3-4b-it-UD-Q4_K_XL.gguf
```

## Step 3: Create Virtual Environment

### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

### Linux/Mac
```bash
python -m venv venv
source venv/bin/activate
```

## Step 4: Install Dependencies

Install the OpenEvolve package and its dependencies:

```bash
pip install --upgrade pip
pip install -e .
```

**Note**: The installation includes `llama-cpp-python` which enables local GGUF model inference.

## Step 5: Verify Installation

Test that the model loads correctly:

```bash
python run_model.py
```

This should load the Gemma model and respond to a test prompt.

## Running OpenEvolve with Gemma

### Linux (Recommended)
Verilog BENCHMARK run:
python3 benchmark_verilog.py --limit 10 --patience 5

Verilog evolve run:
./run_gemma_verilog.sh

Use the provided shell script:
./run_gemma_debug.sh

To clear VRAM cache, run:
pkill -9 python

### Windows
Use the provided batch file:
run_gemma_debug.bat

### Manual Execution

**Full 50-iteration evolution with debug logging:**
python -m openevolve.cli examples/function_minimization/initial_program.py examples/function_minimization/evaluator.py --config examples/function_minimization/gemma_config.yaml --iterations 50 --log-level DEBUG

**Quick test (5 iterations):**
python -m openevolve.cli examples/function_minimization/initial_program.py examples/function_minimization/evaluator.py --config examples/function_minimization/gemma_config.yaml --iterations 5

## Configuration

The Gemma-specific configuration is in `examples/function_minimization/gemma_config.yaml`. Key settings:

- **Model path**: Points to the GGUF file
- **Context window**: Set to 8192 tokens
- **Temperature**: 0.7 for creative evolution
- **Max tokens**: 2048 per generation

## Troubleshooting

### Error: Model file not found
- Ensure `gemma-3-4b-it-UD-Q4_K_XL.gguf` is in the root directory
- Check the path in `gemma_config.yaml` matches your model filename

### Error: No module named 'llama_cpp'
- Run: `pip install llama-cpp-python`

### UnicodeEncodeError on Windows
- The debug script (`run_gemma_debug.bat`) sets `PYTHONIOENCODING=utf-8` to handle emojis in logs

### Slow performance
- The model runs on CPU by default
- For GPU acceleration, install the GPU-enabled version of llama-cpp-python

## Project Structure

GemmaEvolve/
├── gemma-3-4b-it-UD-Q4_K_XL.gguf    # Model file (not in repo)
├── openevolve/                       # Core OpenEvolve package
├── examples/
│   └── function_minimization/        # Example optimization task
│       ├── gemma_config.yaml         # Gemma-specific config
│       ├── initial_program.py        # Starting code
│       └── evaluator.py              # Fitness evaluation
├── run_model.py                      # Test model loading
├── run_gemma_debug.bat              # Windows quick-start script
├── run_gemma_debug.sh               # Linux quick-start script
└── Readme_Gemma.md                  # This file

## Next Steps

- Explore other examples in the `examples/` directory
- Modify `gemma_config.yaml` to experiment with different settings
- Check the OpenEvolve documentation for advanced usage

---

For more information about OpenEvolve, visit the [original repository](https://github.com/algorithmicsuperintelligence/openevolve).
