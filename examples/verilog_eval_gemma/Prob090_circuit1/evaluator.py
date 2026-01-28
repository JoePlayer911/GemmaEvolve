import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model
    using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary Verilog file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
        compile_process = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_process.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_process.stderr
            }

        # Run the simulation using VVP
        simulation_process = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output to determine accuracy
        output = simulation_process.stdout

        if "FAIL" in output:
            # Check if mismatches are parsed
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts from the output
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                accuracy = 1.0  # Assume pass if no mismatches found and no PASS/FAIL

        # Calculate line count
        line_count = len(code.splitlines())

        # Combined score (simple average of accuracy and line count)
        combined_score = (accuracy + line_count / 100.0) / 2.0  # Normalize line count

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
            os.remove("simulation")
        except FileNotFoundError:
            pass