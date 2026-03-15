"""
GGUF (llama.cpp) interface for LLMs
"""

import asyncio
import logging
import os
import time
import json
from typing import Any, Dict, List, Optional

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

from openevolve.llm.base import LLMInterface

logger = logging.getLogger(__name__)


class GGUFLLM(LLMInterface):
    """LLM interface using local GGUF models via llama-cpp-python"""

    def __init__(
        self,
        model_cfg: Optional[Any] = None,
    ):
        if Llama is None:
            raise ImportError(
                "llama-cpp-python is not installed. "
                "Please install it with `pip install llama-cpp-python`."
            )

        self.model = model_cfg.name
        # model_path should be in the config. 
        # If not explicitly provided in model_cfg, we might fallback to checking if 'name' is a path
        self.model_path = getattr(model_cfg, "model_path", None)
        
        if not self.model_path:
            # If name is a file that exists, use it
            if os.path.exists(self.model) and self.model.endswith(".gguf"):
                 self.model_path = self.model
            else:
                 raise ValueError(f"No model_path provided for GGUF model and {self.model} is not a valid path")

        self.system_message = model_cfg.system_message
        self.temperature = model_cfg.temperature
        self.top_p = model_cfg.top_p
        self.max_tokens = model_cfg.max_tokens or 2048
        self.n_ctx = getattr(model_cfg, "n_ctx", 4096)
        
        # Initialize Llama model
        # verbose=False to reduce C++ log spam
        logger.info(f"Loading GGUF model from {self.model_path}...")
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=self.n_ctx,
            verbose=False,
            n_gpu_layers=getattr(model_cfg, "n_gpu_layers", 0) # Default to CPU
        )
        logger.info("GGUF model loaded successfully.")

    def close(self):
        """Explicitly free Llama model resources."""
        if hasattr(self, "llm") and self.llm:
            if hasattr(self.llm, "close"):
                try:
                    self.llm.close()
                except Exception as e:
                    logger.warning(f"Failed to close Llama model: {e}")

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from a prompt"""
        return await self.generate_with_context(
            system_message=self.system_message,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )

    async def generate_with_context(
        self, system_message: str, messages: List[Dict[str, str]], **kwargs
    ) -> str:
        """Generate text using a system message and conversational context"""
        # Prepare messages
        formatted_messages = []
        if system_message:
            formatted_messages.append({"role": "system", "content": system_message})
        
        formatted_messages.extend(messages)

        # Generation parameters
        params = {
            "messages": formatted_messages,
            "temperature": kwargs.get("temperature", self.temperature or 0.7),
            "top_p": kwargs.get("top_p", self.top_p or 0.95),
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
        }

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        try:
            response = await loop.run_in_executor(
                None, lambda: self.llm.create_chat_completion(**params)
            )
            content = response["choices"][0]["message"]["content"]
            
            # --- DEEP LOGGING INTERCEPTOR ---
            try:
                os.makedirs("logs/evolve_generations", exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                # Try to guess problem name from context
                prob_name = "unknown"
                for msg in formatted_messages:
                    if "role" in msg and "content" in msg:
                        if "module" in msg["content"] and "eval" in msg["content"]:
                            # Extremely rough heuristic, but gives us *something*
                            prob_name = "evolution" 
                
                log_path = f"logs/evolve_generations/{timestamp}_{prob_name}.md"
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(f"# OpenEvolve Generation Log - GGUF\n")
                    f.write(f"**Model:** {self.model}\n")
                    f.write(f"**Timestamp:** {timestamp}\n\n")
                    
                    f.write("## Input Context\n\n")
                    for msg in formatted_messages:
                        role = msg.get("role", "unknown")
                        msg_content = msg.get("content", "")
                        f.write(f"### Role: `{role}`\n")
                        f.write("```text\n")
                        f.write(f"{msg_content}\n")
                        f.write("```\n\n")
                        
                    f.write("## LLM Raw Output\n\n")
                    f.write("```text\n")
                    f.write(f"{content}\n")
                    f.write("```\n")
            except Exception as log_err:
                logger.warning(f"Failed to write deep prompt log: {log_err}")
            # --- END DEEP LOGGING ---

            return content
        except Exception as e:
            logger.error(f"Error generating with GGUF model: {e}")
            raise
