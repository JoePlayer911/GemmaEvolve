import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a reference module using Icarus Verilog.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results, including accuracy,
        line count, combined score, and any error messages.
    """
    exec_name = "a.out"
    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Icarus Verilog to compile the design
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True,
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr,
            }

        # Run the simulation
        sim_result = subprocess.run(
            [exec_name], capture_output=True, text=True
        )

        # Parse the simulation output
        output = sim_result.stdout
        accuracy = 1.0
        error_message = ""

        if "FAIL" in output:
            accuracy = 0.0
            mismatches = re.findall(r"Mismatches:\s*(\w+)\s*in\s*(\w+)", output)
            if mismatches:
                accuracy = 0.5  # Example: Penalize for mismatches but don't fail completely
            else:
                accuracy = 0.0

        if "PASS" in output:
            accuracy = 1.0

        if "TIMEOUT" in output:
            accuracy = 0.0
            error_message = "Simulation timed out."

        # Parse mismatch counts if not found with FAIL
        if accuracy == 0.0 and "FAIL" not in output:
            mismatches = re.findall(r"Mismatches:\s*(\w+)\s*in\s*(\w+)", output)
            if mismatches:
                accuracy = 0.5  # Example: Penalize for mismatches but don't fail completely
            else:
                accuracy = 0.0

        # Check for errors in the simulation output
        if "error" in output.lower():
            accuracy = 0.0
            error_message = "Simulation encountered an error."

        # Check for mismatch lines
        mismatch_lines = [line for line in output.splitlines() if "!== (" in line]
        if mismatch_lines:
            accuracy = max(0.0, accuracy - 0.1 * len(mismatch_lines)) # Penalize mismatches.

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": accuracy, # Placeholder for a more complex score
            "error": error_message,
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e),
        }
    finally:
        # Clean up temporary files
        try:
            import os
            os.remove("candidate.sv")
            os.remove(exec_name)
        except FileNotFoundError:
            pass