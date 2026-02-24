import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through a simulation and checking the results.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary Verilog file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "sim", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        sim_cmd = ["vvp", "sim"]
        sim_result = subprocess.run(sim_cmd, capture_output=True, text=True)

        # Parse the simulation output
        output = sim_result.stdout
        accuracy = 1.0
        errors = 0
        mismatches = 0
        errors_f = 0

        if "FAIL" in output:
            accuracy = 0.0

        # Attempt to parse mismatch counts
        match = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if match:
            errors = int(match.group(1))
            mismatches = int(match.group(2))
        
        match_f = re.search(r"errors_f = (\d+)", output)
        if match_f:
            errors_f = int(match_f.group(1))


        if "TIMEOUT" in output:
            accuracy = 0.0

        if errors == 0 and mismatches == 0 and errors_f == 0:
            accuracy = 1.0

        if accuracy == 0.0 and errors > 0:
            accuracy = 1.0 - (errors / mismatches) if mismatches > 0 else 0.0

        # Calculate combined score (simple average of accuracy and line count normalization)
        line_count = len(code.splitlines())
        combined_score = (accuracy + (line_count / 100.0)) / 2.0  # Normalize line count

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("sim")
        except FileNotFoundError:
            pass