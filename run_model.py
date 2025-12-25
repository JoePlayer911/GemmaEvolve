from llama_cpp import Llama
import os

# Define the model path
model_path = "gemma-3-12b-it-Q8_0.gguf"

# Check if model exists
if not os.path.exists(model_path):
    print(f"Error: Model not found at {model_path}")
    exit(1)

print(f"Loading model from {model_path}...")

# Initialize the model
# n_gpu_layers=-1 attempts to offload all layers to the GPU
try:
    llm = Llama(
        model_path=model_path,
        n_gpu_layers=0, # Force CPU
        verbose=True,
        n_ctx=16384 # Adjust context window as needed
    )
except Exception as e:
    print(f"Failed to load model: {e}")
    exit(1)

print("Model loaded successfully!")

# Define a simple prompt
prompt = "<start_of_turn>user\nCreate a simple landing page html<end_of_turn>\n<start_of_turn>model\n"

print("\nGenerating response...")

# Generate output
output = llm(
    prompt,
    max_tokens=256, # Limit response length
    stop=["<end_of_turn>"], 
    echo=True
)

print("-" * 50)
print(output['choices'][0]['text'])
print("-" * 50)
