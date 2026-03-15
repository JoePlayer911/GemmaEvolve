# OpenEvolve: Future Plans & Architecture Thesis

This document serves as a comprehensive reflection on the GemmaEvolve + OpenEvolve benchmark implementation. It chronicles the technical journey, highlighting loose ends, architectural mistakes, pro-tips, and concrete guidance for future development.

## 1. Technical Triumphs & "Aha!" Moments

Throughout the integration of the Verilog benchmark with OpenEvolve, several critical breakthroughs shaped the success of the system:

*   **Deep Prompt Logging is Non-Negotiable:** 
    *   *The Problem:* LLMs fail silently. Initially, OpenEvolve was receiving compilation errors inside its metrics dict but burying them out of the prompt template, causing it to blindly hallucinate solutions without knowing *why* it failed.
    *   *The Fix:* We intercepted `create_chat_completion` directly in `gguf_model.py` and `openai.py` to dump every raw context prompt and raw LLM response into `logs/evolve_generations/`.
    *   *Pro Tip:* Never trust an LLM evaluation loop unless you can manually read the *exact string* being sent to the endpoint.

*   **Cross-Pollination Rescues Stalemates:**
    *   *The Problem:* Islands (parallel evolutionary workers) were originally isolated. If Island 0 went down a bad logic path, it stayed stuck for 800 iterations.
    *   *The Fix:* By modifying `gemma_config.yaml` to set `num_top_programs: 2` and `num_diverse_programs: 1`, we allowed the LLM to inspect successful code from *other* islands, dramatically increasing the solve rate.

*   **Resource Management Trumps Everything in Local LLMs:**
    *   *The Problem:* We experienced massive VRAM memory leaks that crashed the benchmark script between problem evaluations.
    *   *The Fix:* We had to implement explicit `.close()` methods wrapped in `try/except` blocks to force `llama-cpp-python` to release the GPU, alongside Python garbage collection checkpoints.

---

## 2. Identified Mistakes & Anti-Patterns (What We Got Wrong)

*   **Metric Ambiguity (Accuracy vs. Combined Score)**
    *   *Mistake:* The Verilog evaluation script was originally returning a `combined_score` that added a "conciseness bonus" on top of the accuracy score (yielding scores > 1.0).
    *   *Impact:* OpenEvolve's stopping condition was looking for a score of exactly `1.0`. The script overshot this and caused unexpected benchmarking behavior.
    *   *Lesson:* Fitness metrics must be fiercely modular. Keep `accuracy` bounded between `0.0` and `1.0`, and strictly decouple "style/length" scores from semantic correctness.

*   **Rigid Benchmark State Caching**
    *   *Mistake:* Our benchmark resume json (`completion_benchmark.json`) greedily cached early iterations. 
    *   *Impact:* When we fixed critical evaluator bugs (like the `iverilog` silent failure), the benchmark script stubbornly skipped problems it thought were "solved" or "failed" based on broken historical data. 
    *   *Lesson:* Building a forcing flag (`--force-reëval` or scrubbing scripts) is essential when building caching layers over nondeterministic AI executions.

---

## 3. Loose Ends & Unhandled Edge Cases

While the framework is functional, several loose ends remain for future maintainers:

### A. The Nondeterministic Verilog Timeout Edge Case
*   *Loose End:* Some Verilog generations produce extreme infinite loops (e.g. combinatorial loops). Icarus Verilog hangs, triggering Python's `subprocess.TimeoutExpired`.
*   *Action Item:* The LLM needs a specific prompt sub-flag indicating *"Your previous code caused a simulation timeout. Ensure you are not creating combinational loops or hanging the testbench clock."* Currently, `Timeout` is just lumped in as a generic `0.0` accuracy.

### B. Island Diversity Collapse
*   *Loose End:* The system calculates embeddings (via `Nomic-Embed-Code`) to ensure the population stays diverse. However, if the LLM is uncreative, it generates mathematically identical programs that just use different variable names. The embedding similarity might read these as "diverse" when they are semantically identical.
*   *Action Item:* Implement an AST (Abstract Syntax Tree) comparison layer before embedding comparison to aggressively cull functionally identical clones.

### C. GGUF Context Window Constraints
*   *Loose End:* We hard-capped `n_ctx` to 8192 parameters. For massive Verilog examples (like the pipeline processor problems), the system prompt + few-shot examples + artifacts + error traces easily blow past 8K tokens, causing trailing context truncation.
*   *Action Item:* Implement a smart context-summarizer. If artifacts exceed 2000 tokens, use an LLM pre-pass to summarize the testbench failures before feeding it to the main OpenEvolve generator.

---

## 4. How-To: Future Extensions

### Adding a New Language (e.g., Python / C++)
To extend OpenEvolve beyond Verilog:
1.  **Duplicate `scripts/convert_problems.py`**: Modify the regex logic that looks for `iverilog` to instead look for `pytest` or `gcc`.
2.  **Update `evaluator.py` Generation**: Replace the `vvp` subprocess logic with the native execution wrapper for the new language. Ensure the return dict perfectly respects: `{"accuracy": 0.0 - 1.0, "error": Optional[str]}`.
3.  **Prompt Reframing**: Update the `system_message` in the `gemma_config.yaml` to provide language-specific architectural advice.

### Implementing a True "Cactus Plot" Visualization
Currently, `completion_benchmark_results_chart.py` explicitly lists the hardest 17 problems horizontally.
*   *Extension:* If the dataset grows to 1000+ problems, a horizontal bar chart will fail.
*   *How-to:* Switch to a bounded scatter plot. Map X-Axis = `Rank (1 to N)` and Y-Axis = `Iterations to Solve`. This creates the classic hardware-verification "cactus plot" showing the exponential cliff where the LLM stops being able to solve problems.
