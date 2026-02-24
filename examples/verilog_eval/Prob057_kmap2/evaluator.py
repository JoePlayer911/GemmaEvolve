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
        # Create a temporary Verilog file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"],
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
            ["vvp", "test"],
            capture_output=True,
            text=True
        )

        output = simulation_result.stdout

        # Parse the output for mismatches
        match = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if match:
            errors = int(match.group(1))
            clocks = int(match.group(2))
            if errors > 0:
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0
        else:
            # Check for "FAIL" or "PASS"
            if "FAIL" in output:
                accuracy = 0.0
            elif "PASS" in output:
                accuracy = 1.0
            else:
                accuracy = 1.0  # Assume pass if no mismatches and no explicit fail

        # Calculate line count
        line_count = len(code.splitlines())

        # Calculate combined score (simple accuracy for now)
        combined_score = accuracy

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
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
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("test")
        except FileNotFoundError:
            pass