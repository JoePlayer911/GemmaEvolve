import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        exec_name = "a.out"
        candidate_name = "candidate.v"
        ref_name = "testbench.sv"

        with open(candidate_name, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, candidate_name, ref_name],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        sim_result = subprocess.run(
            [exec_name],
            capture_output=True,
            text=True
        )

        output = sim_result.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
                return {
                    "accuracy": accuracy,
                    "line_count": len(code.splitlines()),
                    "combined_score": accuracy,
                    "error": ""
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": len(code.splitlines()),
                    "combined_score": 0.0,
                    "error": ""
                }

        # Check for "PASS" or mismatches
        if "PASS" in output:
            return {
                "accuracy": 1.0,
                "line_count": len(code.splitlines()),
                "combined_score": 1.0,
                "error": ""
            }

        # Parse mismatches
        mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches:
            errors = int(mismatches.group(1))
            total_samples = int(mismatches.group(2))
            accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            return {
                "accuracy": accuracy,
                "line_count": len(code.splitlines()),
                "combined_score": accuracy,
                "error": ""
            }

        return {
            "accuracy": 1.0,
            "line_count": len(code.splitlines()),
            "combined_score": 1.0,
            "error": ""
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up generated files
        import os
        try:
            os.remove(candidate_name)
            os.remove(exec_name)
        except FileNotFoundError:
            pass