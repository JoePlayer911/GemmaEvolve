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
        # Write the candidate code to a temporary file
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
                "error": f"Compilation failed: {compile_result.stderr}"
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

        if "FAIL" in output:
            errors = re.findall(r"Mismatches: (\d+) in (\d+)", output)
            if errors:
                mismatches, samples = map(int, errors[0])
                accuracy = 1.0 - (mismatches / samples)
                return {
                    "accuracy": accuracy,
                    "line_count": line_count,
                    "combined_score": accuracy,
                    "error": None
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": line_count,
                    "combined_score": 0.0,
                    "error": None
                }

        if "PASS" in output:
            return {
                "accuracy": 1.0,
                "line_count": line_count,
                "combined_score": 1.0,
                "error": None
            }

        # Parse mismatch counts if present
        errors = re.findall(r"Mismatches: (\d+) in (\d+)", output)
        if errors:
            mismatches, samples = map(int, errors[0])
            accuracy = 1.0 - (mismatches / samples)
            return {
                "accuracy": accuracy,
                "line_count": line_count,
                "combined_score": accuracy,
                "error": None
            }
        else:
            return {
                "accuracy": 1.0,
                "line_count": line_count,
                "combined_score": 1.0,
                "error": None
            }
    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
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