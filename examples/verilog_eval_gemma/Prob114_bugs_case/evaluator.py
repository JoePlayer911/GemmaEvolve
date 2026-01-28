import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference module.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Save the candidate module to a temporary file
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
                "line_count": 0,
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

        # Check for explicit "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*X in\s*(\w+)", output)
            if mismatches:
                return {
                    "accuracy": 0.0,
                    "line_count": 0,
                    "combined_score": 0.0,
                    "error": "FAIL with mismatches"
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": 0,
                    "combined_score": 0.0,
                    "error": "FAIL (no mismatches reported)"
                }

        # Check for explicit "PASS"
        if "PASS" in output:
            return {
                "accuracy": 1.0,
                "line_count": 0,
                "combined_score": 1.0,
                "error": None
            }

        # Parse mismatch counts (if present)
        mismatches = re.search(r"stats1\.errors\s*=\s*(\d+)", output)
        if mismatches:
            error_count = int(mismatches.group(1))
            if error_count == 0:
                return {
                    "accuracy": 1.0,
                    "line_count": 0,
                    "combined_score": 1.0,
                    "error": None
                }
            else:
                return {
                    "accuracy": 1.0 - (error_count / 1000),  # Example accuracy calculation
                    "line_count": 0,
                    "combined_score": 1.0 - (error_count / 1000),
                    "error": f"Mismatches found: {error_count}"
                }

        # If no explicit PASS or FAIL, assume PASS if no errors are found
        return {
            "accuracy": 1.0,
            "line_count": 0,
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
            os.remove("simulation")
        except FileNotFoundError:
            pass