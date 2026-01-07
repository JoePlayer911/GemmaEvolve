import sys
import os
from llama_cpp import Llama

# Configure to use 2 GPUs
os.environ["CUDA_VISIBLE_DEVICES"] = "0,1"
print(f"CUDA_VISIBLE_DEVICES set to: {os.environ['CUDA_VISIBLE_DEVICES']}")

model_path = "/home/jonathan13/GemmaEvolve/gemma-3-12b-it-Q8_0.gguf"

if not os.path.exists(model_path):
    print(f"Model file not found: {model_path}")
    sys.exit(1)

print(f"Loading model from {model_path}...")
try:
    # n_gpu_layers=-1 to offload all layers to available GPUs
    # main_gpu=0 specifies the main GPU
    # split_mode=1 (LLAMA_SPLIT_MODE_LAYER) is default usually, let's stick to defaults first
    llm = Llama(
        model_path=model_path,
        n_ctx=8192,
        verbose=True,
        n_gpu_layers=-1
    )
    print("Model loaded successfully")
    
    # Simple generation test
    output = llm("Hello, verify you are running on multiple GPUs if possible.", max_tokens=20)
    print(f"Output: {output}")
    
except Exception as e:
    print(f"Error loading model: {e}")
    import traceback
    traceback.print_exc()
