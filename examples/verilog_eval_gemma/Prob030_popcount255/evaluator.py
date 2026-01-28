import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module using iverilog and vvp.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
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
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(code.splitlines())
        accuracy = 1.0
        error_message = ""

        if "FAIL" in output:
            accuracy = 0.0

        # Parse mismatch counts
        mismatches_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches_pattern:
            errors = int(mismatches_pattern.group(1))
            clocks = int(mismatches_pattern.group(2))
            if errors > 0:
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0

        elif "TIMEOUT" in output:
            accuracy = 0.0

        elif "errors" in output:
             errors_pattern = re.search(r"stats1\.errors=(\d+)", output)
             if errors_pattern:
                errors = int(errors_pattern.group(1))
                clocks_pattern = re.search(r"stats1\.clocks=(\d+)", output)
                if clocks_pattern:
                   clocks = int(clocks_pattern.group(1))
                   if errors > 0:
                      accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0

        if "ERROR" in compile_result.stderr:
            error_message = compile_result.stderr

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": accuracy,
            "error": error_message
        }

    except FileNotFoundError as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": f"Error: iverilog or vvp not found. Please ensure they are installed and in your PATH. {e}"
        }
    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": 0,
            "combined_score": 0.0,
            "error": f"An unexpected error occurred: {e}"
        }
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("simulation")
        except FileNotFoundError:
            pass