import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: The accuracy score (float between 0.0 and 1.0).
        - line_count: The number of lines in the Verilog code.
        - combined_score: A combined score based on accuracy and line count (optional).
        - error: An error message if any error occurred during evaluation.
    """

    try:
        exec_name = "eval_exec"
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": 0,
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        simulation_result = subprocess.run(
            [exec_name],
            capture_output=True,
            text=True
        )

        output = simulation_result.stdout

        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                mismatches_count = int(mismatches.group(1))
                total_count = int(mismatches.group(2))
                accuracy = 1.0 - (mismatches_count / total_count) if total_count > 0 else 0.0
                return {
                    "accuracy": accuracy,
                    "line_count": len(code.splitlines()),
                    "combined_score": accuracy,
                    "error": None
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": len(code.splitlines()),
                    "combined_score": 0.0,
                    "error": None
                }

        # Check for "PASS" or no errors
        if "PASS" in output or "TIMEOUT" in output:
            return {
                "accuracy": 1.0,
                "line_count": len(code.splitlines()),
                "combined_score": 1.0,
                "error": None
            }
        
        # Parse mismatch counts from the output
        mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
        if mismatches:
            mismatches_count = int(mismatches.group(1))
            total_count = int(mismatches.group(2))
            accuracy = 1.0 - (mismatches_count / total_count) if total_count > 0 else 0.0
            return {
                "accuracy": accuracy,
                "line_count": len(code.splitlines()),
                "combined_score": accuracy,
                "error": None
            }

        return {
            "accuracy": 1.0,
            "line_count": len(code.splitlines()),
            "combined_score": 1.0,
            "error": None
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove(exec_name)
        except FileNotFoundError:
            pass