
import asyncio
import logging
import sys

# Add project root to path
sys.path.insert(0, "e:\\Project\\AI\\GemmaEvolve")

import openevolve.config
print(f"Loaded config from: {openevolve.config.__file__}")

from openevolve.config import LLMModelConfig
from openevolve.llm.ensemble import LLMEnsemble

# Configure logging
logging.basicConfig(level=logging.INFO)

async def main():
    print("Testing GGUF Integration...")

    # Path to the GGUF model - using the one from user request
    model_path = "e:\\Project\\AI\\GemmaEvolve\\gemma-3-4b-it-UD-Q4_K_XL.gguf"
    
    # Configure model
    config = LLMModelConfig(
        name="gemma-local",
        model_path=model_path,
        n_ctx=2048,
        n_gpu_layers=0, # Force CPU
        temperature=0.7,
        max_tokens=100
    )

    print(f"Initializing ensemble with model at: {model_path}")
    ensemble = LLMEnsemble([config])

    prompt = "Explain quantum computing in one sentence."
    print(f"\nPrompt: {prompt}")

    try:
        response = await ensemble.generate(prompt)
        print(f"\nResponse:\n{response}")
        print("\nSUCCESS: Model generated a response.")
    except Exception as e:
        print(f"\nFAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
