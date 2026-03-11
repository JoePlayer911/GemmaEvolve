
import os
import sys
import time
import json
import yaml
import subprocess
import glob
import re
import argparse
import importlib.util
import threading
from datetime import datetime
from typing import Dict, Any, List

# Try to import llama_cpp
try:
    from llama_cpp import Llama
except ImportError:
    print("Warning: llama-cpp-python not found. Pure Gemma baseline will fail if attempted.")
    Llama = None

# Configuration defaults
DEFAULT_MODEL_PATH = "/home/jonathan13/GemmaEvolve/gemma-3-12b-it-Q8_0.gguf"
DATASET_DIR = "examples/verilog_eval"
RESULTS_FILE = "completion_benchmark.json"
LOGS_DIR = "logs"

SCORE_THRESHOLD = 1.0  # Only run OpenEvolve if Gemma scores below this
DEFAULT_MAX_ITERATIONS = 800   # Default iteration limit for OpenEvolve
DEFAULT_CHECKPOINT_INTERVAL = 100  # Default frequency to save checkpoint
BASELINE_TIMEOUT = 120  # Timeout in seconds for baseline Gemma generation


def load_config(config_path):
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_pure_gemma(llm, problem_dir: str, config_path: str) -> Dict[str, Any]:
    """Runs a zero-shot attempt using the raw Gemma model."""
    start_time = time.time()

    # Load config to get the prompt
    config = load_config(config_path)
    system_msg = config['prompt']['system_message']

    # Construct a simple zero-shot prompt
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": "Please implement the module described above. Output ONLY the Verilog code."}
    ]

    generated_code = ""
    try:
        response_generator = llm.create_chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=4096,
            stream=True
        )
        
        for chunk in response_generator:
            if time.time() - start_time > BASELINE_TIMEOUT:
                print(f"  WARNING: Gemma generation timed out after {BASELINE_TIMEOUT}s")
                # Need to manually close the generator to ensure llamacpp stops cleanly
                response_generator.close()
                return {
                    "score": 0.0, "accuracy": 0.0,
                    "time": time.time() - start_time,
                    "mode": "pure_gemma_timeout"
                }

            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                if "content" in delta and delta["content"] is not None:
                    generated_code += delta["content"]
                    
    except Exception as e:
        raise e

    # Extract code if wrapped in markdown
    if "```verilog" in generated_code:
        generated_code = generated_code.split("```verilog")[1].split("```")[0].strip()
    elif "```" in generated_code:
        generated_code = generated_code.split("```")[1].split("```")[0].strip()

    execution_time = time.time() - start_time

    # Evaluate
    evaluator_path = os.path.join(problem_dir, "evaluator.py")
    spec = importlib.util.spec_from_file_location("evaluator", evaluator_path)
    evaluator_module = importlib.util.module_from_spec(spec)
    sys.modules["evaluator"] = evaluator_module
    spec.loader.exec_module(evaluator_module)

    # Run evaluation inside the problem directory to resolve relative paths (testbench.sv)
    original_cwd = os.getcwd()
    os.chdir(problem_dir)
    try:
        result = evaluator_module.evaluate(generated_code)
    finally:
        os.chdir(original_cwd)

    # Save baseline generated code
    code_path = os.path.join(problem_dir, "baseline_generated.v")
    with open(code_path, "w") as f:
        f.write(generated_code)

    return {
        "score": result.get("combined_score", 0.0),
        "accuracy": result.get("accuracy", 0.0),
        "time": execution_time,
        "mode": "pure_gemma",
        "code_path": code_path
    }


def parse_log_checkpoints(log_filename: str, checkpoints: List[int] = None) -> Dict[str, Dict[str, float]]:
    """Parse an OpenEvolve log to extract best-so-far score at each checkpoint iteration.

    Returns a dict like:
        {"iter_100": {"score": 0.5, "accuracy": 0.5},
         "iter_200": {"score": 0.8, "accuracy": 0.8}, ...}
    """
    if checkpoints is None:
        checkpoints = CHECKPOINTS

    # Regex patterns
    iter_pattern = re.compile(r'Iteration (\d+):')
    iter_time_pattern = re.compile(r'Iteration \d+: .* completed in ([\d.]+)s')
    metrics_pattern = re.compile(r'Metrics:.*?accuracy=([\d.]+).*?combined_score=([\d.]+)')
    best_pattern = re.compile(r'New best score: ([\d.]+)')
    target_pattern = re.compile(r'Target score .* reached at iteration (\d+)')
    early_stop_pattern = re.compile(r'\[STOP\].*at iteration (\d+)')

    best_score = 0.0
    best_accuracy = 0.0
    current_iter = 0
    max_reached_iter = 0
    solved_iteration = None
    solved_time = 0.0
    checkpoint_results = {}

    # Need checkpoint values to accurately build the range if not provided
    if not checkpoints:
         checkpoints = []

    try:
        with open(log_filename, 'r') as f:
            for line in f:
                # Track current iteration
                m = iter_pattern.search(line)
                if m:
                    current_iter = int(m.group(1))
                    max_reached_iter = max(max_reached_iter, current_iter)
                
                time_match = iter_time_pattern.search(line)
                if time_match:
                    solved_time += float(time_match.group(1))

                # Also extract metrics from the same Metrics line
                mm = metrics_pattern.search(line)
                if mm:
                    acc = float(mm.group(1))
                    score = float(mm.group(2))
                    if score > best_score:
                        best_score = score
                        best_accuracy = acc

                # Check for "New best score" lines
                m = best_pattern.search(line)
                if m:
                    new_best = float(m.group(1))
                    if new_best > best_score:
                        best_score = new_best

                # Check for metrics on separate lines
                if 'Metrics:' in line and 'Iteration' not in line:
                    mm = metrics_pattern.search(line)
                    if mm:
                        acc = float(mm.group(1))
                        score = float(mm.group(2))
                        if score > best_score:
                            best_score = score
                            best_accuracy = acc

                # Record checkpoint when we cross a boundary
                for cp in checkpoints:
                    if current_iter >= cp and f"iter_{cp}" not in checkpoint_results:
                        checkpoint_results[f"iter_{cp}"] = {
                            "score": best_score,
                            "accuracy": best_accuracy
                        }

                # Track early stop / target reached
                m = target_pattern.search(line)
                if m:
                    solved_iteration = int(m.group(1))
                    max_reached_iter = max(max_reached_iter, solved_iteration)
                m = early_stop_pattern.search(line)
                if m:
                    max_reached_iter = max(max_reached_iter, int(m.group(1)))
    except Exception as e:
        print(f"  WARNING: Error parsing log {log_filename}: {e}")

    # Fill remaining checkpoints beyond what was reached (use the last known best)
    for cp in checkpoints:
        key = f"iter_{cp}"
        if key not in checkpoint_results:
            # If we ran past this iteration but didn't record it, use current best
            if max_reached_iter >= cp:
                checkpoint_results[key] = {
                    "score": best_score,
                    "accuracy": best_accuracy
                }
            else:
                # OpenEvolve stopped before reaching this checkpoint
                # Use the best score at the time of stopping
                checkpoint_results[key] = {
                    "score": best_score,
                    "accuracy": best_accuracy
                }

    checkpoint_results["metadata"] = {
        "solved_iteration": solved_iteration,
        "solved_time_seconds": round(solved_time, 2) if solved_iteration else None
    }

    return checkpoint_results


def run_openevolve(problem_dir: str, config_path: str, max_iterations: int, save_freq: int,
                   jumpstart_path: str = None, prob_name: str = "unknown") -> Dict[str, Any]:
    """Runs OpenEvolve via subprocess with config parameters."""
    start_time = time.time()

    # Create a temporary config - enable target score stopping
    config = load_config(config_path)
    config['target_score'] = 1.0        # Stop when combined score hits 1.0 (accuracy 1.0 + optimization)
    config['early_stopping_patience'] = 99999  # Disable early stopping (large number)

    temp_config_path = os.path.join(problem_dir, "gemma_config_benchmark.yaml")
    with open(temp_config_path, 'w') as f:
        yaml.dump(config, f)

    if jumpstart_path and os.path.exists(jumpstart_path):
        initial_program = jumpstart_path
        print(f"  Jump-starting OpenEvolve with baseline code: {initial_program}")
    else:
        initial_program = os.path.join(problem_dir, "initial_program.v")

    remaining_iterations = max_iterations

    cmd = [
        sys.executable, "-m", "openevolve.cli",
        initial_program,
        evaluator_script,
        "--config", temp_config_path,
        "--checkpoint-interval", str(save_freq),
        "--log-level", "DEBUG"
    ]

    # Auto-resume logic
    checkpoint_dir = os.path.join(problem_dir, "openevolve_output", "checkpoints")
    if os.path.exists(checkpoint_dir):
        existing_checkpoints = [
            d for d in os.listdir(checkpoint_dir)
            if os.path.isdir(os.path.join(checkpoint_dir, d)) and d.startswith("checkpoint_")
        ]
        if existing_checkpoints:
            # Sort by iteration number
            latest_cp = sorted(existing_checkpoints, key=lambda x: int(x.split("_")[-1]))[-1]
            latest_iter = int(latest_cp.split("_")[-1])
            
            # Use checkpoint path to resume
            cp_path = os.path.join(checkpoint_dir, latest_cp)
            cmd.extend(["--checkpoint", cp_path])
            
            # Calculate remaining iterations to achieve total max_iterations
            remaining_iterations = max(0, max_iterations - latest_iter)
            print(f"  Found existing checkpoint {latest_cp}. Resuming OpenEvolve from iteration {latest_iter} (running {remaining_iterations} more)...")

            if remaining_iterations == 0:
                print(f"  Already reached {max_iterations} iterations at {latest_cp}. Not running OpenEvolve.")
                # We can just return immediately or run for 0 iterations to parse the log. 
                # OpenEvolve handles 0 iterations by just exiting gracefully.
                
    cmd.extend(["--iterations", str(remaining_iterations)])

    # Create timestamped log file
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(LOGS_DIR, f"completion_{prob_name}_{timestamp}.log")
    print(f"  Logging DEBUG output to: {log_filename}")

    # Run process, streaming all output to the log file
    try:
        with open(log_filename, "w") as logfile:
            logfile.write(f"=== Completion Benchmark - OpenEvolve Log ===\n")
            logfile.write(f"Problem: {prob_name}\n")
            logfile.write(f"Timestamp: {timestamp}\n")
            logfile.write(f"Initial Program: {initial_program}\n")
            logfile.write(f"Config: {temp_config_path}\n")
            logfile.write(f"Iteration Limit: {max_iterations}\n")
            logfile.write(f"Command: {' '.join(cmd)}\n")
            logfile.write(f"{'=' * 60}\n\n")
            logfile.flush()
            result = subprocess.run(cmd, check=True, stdout=logfile, stderr=subprocess.STDOUT, text=True)
    except subprocess.CalledProcessError as e:
        print(f"  OpenEvolve failed with exit code {e.returncode}")
        print(f"  Check log file for details: {log_filename}")
        return {"mode": "openevolve_error", "log": log_filename}
    finally:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)

    execution_time = time.time() - start_time

    # Build expected checkpoints list based on max_iterations and save_freq
    expected_checkpoints = list(range(save_freq, max_iterations + 1, save_freq))
    
    # Parse the log to extract checkpoint scores
    checkpoint_scores = parse_log_checkpoints(log_filename, checkpoints=expected_checkpoints)
    metadata = checkpoint_scores.pop("metadata", {})

    # Also read final best result from output dir for authoritative final score
    output_dir = os.path.join(problem_dir, "openevolve_output")
    best_info_path = os.path.join(output_dir, "best", "best_program_info.json")

    if os.path.exists(best_info_path):
        with open(best_info_path, 'r') as f:
            info = json.load(f)
            metrics = info.get("metrics", {})
            final_score = metrics.get("combined_score", 0.0)
            final_accuracy = metrics.get("accuracy", 0.0)
            # Override the last checkpoint with the authoritative final result
            last_key = f"iter_{max_iterations}"
            if last_key in checkpoint_scores:
                checkpoint_scores[last_key] = {
                    "score": final_score,
                    "accuracy": final_accuracy
                }

    result = {
        **checkpoint_scores,
        "solved_iteration": metadata.get("solved_iteration"),
        "total_time": execution_time,
        "mode": "openevolve",
        "log": log_filename,
        "start_iteration": latest_iter if 'latest_iter' in locals() else 0
    }

    return result


def deduplicate_results(results: List[Dict]) -> List[Dict]:
    """Remove duplicate entries, keeping the last successful run for each problem."""
    seen = {}
    for entry in results:
        prob = entry["problem"]
        # If we already have this problem, keep the one with a non-error mode
        if prob in seen:
            existing = seen[prob]
            existing_is_error = existing.get("baseline", {}).get("mode", "").endswith("_error")
            new_is_error = entry.get("baseline", {}).get("mode", "").endswith("_error")
            if existing_is_error and not new_is_error:
                seen[prob] = entry  # Replace error entry with successful one
            # Otherwise keep existing (first successful, or first error if both error)
        else:
            seen[prob] = entry
    return list(seen.values())


def sort_results_by_problem_number(results: List[Dict]) -> List[Dict]:
    """Sort results by problem number (numeric extraction from Prob###_name)."""
    def sort_key(entry):
        m = re.search(r'Prob(\d+)', entry.get('problem', ''))
        return int(m.group(1)) if m else 999
    return sorted(results, key=sort_key)


def main():
    parser = argparse.ArgumentParser(description="Completion Benchmark: OpenEvolve vs Native Gemma (Multi-Checkpoint)")
    parser.add_argument("--limit", type=int, default=0, help="Number of problems to run (0 = all)")
    parser.add_argument("--iterations", type=int, default=DEFAULT_MAX_ITERATIONS, help=f"Total iterations to run OpenEvolve (default: {DEFAULT_MAX_ITERATIONS})")
    parser.add_argument("--save-freq", type=int, default=DEFAULT_CHECKPOINT_INTERVAL, help=f"How often to save checkpoint state (default: {DEFAULT_CHECKPOINT_INTERVAL})")
    parser.add_argument("--jumpstart", action="store_true", default=False,
                        help="Use native Gemma baseline output as initial program for OpenEvolve (default: disabled)")
    parser.add_argument("--start", type=int, default=1,
                        help="Positional index to start from (1-indexed into sorted dir list, NOT problem number). Previous results are preserved.")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for LLM generation (default: 42)")
    parser.add_argument("--fill-gaps", action="store_true", default=False,
                        help="Auto-detect problems missing from results JSON and run only those.")
    parser.add_argument("--deduplicate", action="store_true", default=False,
                        help="Remove duplicate error entries from results JSON (keeps successful re-runs).")
    args = parser.parse_args()

    if not os.path.exists(DATASET_DIR):
        print(f"Error: Dataset {DATASET_DIR} not found.")
        return

    # Handle --deduplicate mode (standalone operation)
    if args.deduplicate:
        if not os.path.exists(RESULTS_FILE):
            print(f"Error: {RESULTS_FILE} not found.")
            return
        with open(RESULTS_FILE, 'r') as f:
            existing = json.load(f)
        print(f"  Before dedup: {len(existing)} entries")
        deduped = deduplicate_results(existing)
        sorted_results = sort_results_by_problem_number(deduped)
        print(f"  After dedup:  {len(sorted_results)} entries")
        with open(RESULTS_FILE, 'w') as f:
            json.dump(sorted_results, f, indent=2)
        print(f"  Saved to {RESULTS_FILE}")
        if not args.fill_gaps:
            return

    # We will lazy-load the baseline LLM to allow freeing memory for OpenEvolve
    llm = None

    all_problems = sorted(glob.glob(os.path.join(DATASET_DIR, "Prob*")))

    # Handle --fill-gaps mode: only run missing problems
    if args.fill_gaps:
        if not os.path.exists(RESULTS_FILE):
            print(f"No existing {RESULTS_FILE}. Running all problems instead.")
            problems = all_problems
        else:
            with open(RESULTS_FILE, 'r') as f:
                existing_results = json.load(f)
            # Deduplicate first
            existing_results = deduplicate_results(existing_results)
            # Find which problems already have non-error results
            completed_problems = set()
            for entry in existing_results:
                baseline_mode = entry.get("baseline", {}).get("mode", "")
                if not baseline_mode.endswith("_error"):
                    completed_problems.add(entry["problem"])
            # Filter to only missing problems
            problems = [p for p in all_problems if os.path.basename(p) not in completed_problems]
            if not problems:
                print(f"  All problems already have results in {RESULTS_FILE}. Nothing to do.")
                return
            print(f"  Found {len(problems)} missing problems to fill:")
            for p in problems:
                print(f"    - {os.path.basename(p)}")
            print()
    else:
        problems = all_problems

    total_problems = len(problems) if args.limit == 0 else min(len(problems), args.limit)
    results = []

    # Counters for summary
    gemma_solved = 0
    gemma_failed = 0
    openevolve_attempted = 0
    openevolve_solved = 0
    skipped_errors = 0

    # Resume support (only for non-fill-gaps mode): load existing results and reconstruct counters
    start_idx = args.start - 1 if not args.fill_gaps else 0  # fill-gaps handles its own filtering
    if start_idx > 0 and os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as f:
            existing_results = json.load(f)
        # Keep results up to (but not including) the start index
        results = existing_results[:start_idx]
        # Reconstruct counters from loaded results
        for r in results:
            if r.get("gemma_solved", False):
                gemma_solved += 1
            else:
                gemma_failed += 1
                oe = r.get("openevolve", {})
                if isinstance(oe, dict) and oe.get("mode") != "openevolve_error":
                    openevolve_attempted += 1
                    if r.get("openevolve_solved", False):
                        openevolve_solved += 1
        print(f"  Resuming from problem {args.start}. Loaded {len(results)} previous results.")


    # Build checkpoint labels locally since global CHECKPOINTS is gone
    checkpoints = list(range(args.save_freq, args.iterations + 1, args.save_freq))
    checkpoint_labels = [f"iter_{cp}" for cp in checkpoints]

    print(f"\n{'=' * 70}")
    print(f"  COMPLETION BENCHMARK (Multi-Checkpoint)")
    if args.fill_gaps:
        print(f"  Mode: FILL GAPS ({total_problems} missing problems)")
    print(f"  Problems: {total_problems} | Iterations: {args.iterations} | Save Freq: {args.save_freq}")
    print(f"  Checkpoints: {checkpoints}")
    print(f"  Strategy: Run OpenEvolve ONLY when Gemma scores < {SCORE_THRESHOLD}")
    if start_idx > 0:
        print(f"  Resuming from: Problem {args.start}")
    print(f"{'=' * 70}\n")

    for i, problem_dir in enumerate(problems):
        if args.limit > 0 and i >= total_problems:
            break
        if not args.fill_gaps and i < start_idx:
            continue

        prob_name = os.path.basename(problem_dir)
        config_path = os.path.join(problem_dir, "gemma_config.yaml")

        print(f"\n[{i+1}/{total_problems}] --- {prob_name} ---")

        # 1. Pure Gemma Baseline
        print(f"  Running Native Gemma...")
        try:
            if llm is None:
                print("  Loading Gemma model for Baseline...")
                llm = Llama(
                    model_path=DEFAULT_MODEL_PATH,
                    n_ctx=32768,
                    n_gpu_layers=-1,  # GPU for fast inference
                    seed=args.seed,
                    verbose=False
                )
            baseline_res = run_pure_gemma(llm, problem_dir, config_path)
        except Exception as e:
            print(f"  ERROR running Gemma: {e}")
            print(f"  ⚠ SKIPPING {prob_name} (baseline error)")
            skipped_errors += 1
            continue
        print(f"  Gemma Score: {baseline_res['score']:.4f} (accuracy={baseline_res.get('accuracy', 0):.4f})")

        entry = {
            "problem": prob_name,
            "baseline": baseline_res,
        }

        # 2. Check if Gemma already solved it
        if baseline_res['score'] >= SCORE_THRESHOLD:
            gemma_solved += 1
            entry["openevolve"] = "skipped"
            entry["gemma_solved"] = True
            print(f"  ✓ Gemma solved it (score >= {SCORE_THRESHOLD}). Skipping OpenEvolve.")
        else:
            gemma_failed += 1
            print(f"  ✗ Gemma failed (score < {SCORE_THRESHOLD}). Running OpenEvolve ({args.iterations} iterations)...")

            # Free up baseline LLM VRAM before spawning OpenEvolve
            if llm is not None:
                if hasattr(llm, 'close'):
                    try:
                        llm.close()
                    except Exception as e:
                        print(f"  Warning: llm.close() failed: {e}")
                del llm
                import gc
                gc.collect()
                llm = None

            jumpstart_code = baseline_res.get('code_path') if args.jumpstart else None
            try:
                evolve_res = run_openevolve(
                    problem_dir, config_path, args.iterations, args.save_freq,
                    jumpstart_path=jumpstart_code, prob_name=prob_name
                )

                # Check if OpenEvolve errored
                if evolve_res.get("mode") == "openevolve_error":
                    print(f"  ⚠ SKIPPING {prob_name} (OpenEvolve error)")
                    skipped_errors += 1
                    continue

                openevolve_attempted += 1

                # Print checkpoint scores
                print(f"  OpenEvolve Checkpoint Scores:")
                for cp in checkpoints:
                    key = f"iter_{cp}"
                    cp_data = evolve_res.get(key, {})
                    score = cp_data.get("score", 0.0)
                    acc = cp_data.get("accuracy", 0.0)
                    print(f"    Iter {cp:4d}: score={score:.4f}, accuracy={acc:.4f}")
                print(f"  Total time: {evolve_res.get('total_time', 0):.1f}s")

                entry["openevolve"] = evolve_res
                entry["gemma_solved"] = False

                # Check if any checkpoint solved it
                final_cp = evolve_res.get(f"iter_{args.iterations}", {})
                final_score = final_cp.get("score", 0.0)
                entry["openevolve_solved"] = final_score >= SCORE_THRESHOLD

                if final_score >= SCORE_THRESHOLD:
                    openevolve_solved += 1
                    print(f"  ✓ OpenEvolve COMPLETED the problem!")
                else:
                    print(f"  ✗ OpenEvolve could not fully solve it either.")
            except Exception as e:
                print(f"  ERROR running OpenEvolve: {e}")
                print(f"  ⚠ SKIPPING {prob_name} (OpenEvolve exception)")
                skipped_errors += 1
                continue

        results.append(entry)

        # Save incrementally (in case of crash)
        if args.fill_gaps:
            # In fill-gaps mode, merge new results into existing file
            if os.path.exists(RESULTS_FILE):
                with open(RESULTS_FILE, 'r') as f:
                    all_results = json.load(f)
            else:
                all_results = []
            all_results.append(entry)
            all_results = deduplicate_results(all_results)
            all_results = sort_results_by_problem_number(all_results)
            with open(RESULTS_FILE, 'w') as f:
                json.dump(all_results, f, indent=2)
        else:
            with open(RESULTS_FILE, 'w') as f:
                json.dump(results, f, indent=2)

    # Final Summary
    print(f"\n{'=' * 70}")
    print(f"  COMPLETION BENCHMARK RESULTS (Multi-Checkpoint)")
    print(f"{'=' * 70}")
    print(f"  Total problems tested:          {len(results)}")
    print(f"  Skipped (errors):               {skipped_errors}")
    print(f"  Gemma solved (score >= 1.0):     {gemma_solved}")
    print(f"  Gemma failed (score <  1.0):     {gemma_failed}")
    print(f"  OpenEvolve attempted:            {openevolve_attempted}")
    print(f"  OpenEvolve solved (@ iter {args.iterations}):  {openevolve_solved}")
    if openevolve_attempted > 0:
        print(f"  OpenEvolve completion rate:      {openevolve_solved}/{openevolve_attempted} ({100*openevolve_solved/openevolve_attempted:.1f}%)")
    print(f"{'=' * 70}")

    # Detailed table for failed problems with checkpoint progression
    failed_entries = [r for r in results if not r.get("gemma_solved", False)]
    if failed_entries:
        header = f"{'Problem':<25} | {'Gemma':>8}"
        for cp in checkpoints:
            header += f" | {'@'+str(cp):>8}"
        header += f" | {'Solved Iter':>11}"
        print(f"\n--- Detailed Results: Problems Gemma Could NOT Solve ---")
        print(header)
        print("-" * len(header))
        for entry in failed_entries:
            gemma_score = entry['baseline']['score']
            oe = entry.get('openevolve', {})
            row = f"{entry['problem']:<25} | {gemma_score:>8.4f}"
            if isinstance(oe, dict) and oe.get("mode") != "openevolve_error":
                for cp in checkpoints:
                    key = f"iter_{cp}"
                    cp_data = oe.get(key, {})
                    score = cp_data.get("score", 0.0)
                    row += f" | {score:>8.4f}"
                
                solved_iter = oe.get("solved_iteration")
                if solved_iter:
                    row += f" | {solved_iter:>11d}"
                else:
                    row += f" | {'-':>11}"
            else:
                for cp in checkpoints:
                    row += f" | {'N/A':>8}"
                row += f" | {'N/A':>11}"
            print(row)

    print(f"\nResults saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
