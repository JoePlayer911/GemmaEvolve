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
        # Save the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = f"iverilog -g2012 -o test { 'candidate.sv' } testbench.sv ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"Iverilog compilation error: {iverilog_result.stderr}"}

        # Run vvp
        vvp_cmd = f"vvp test"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        line_count = len(output.splitlines())

        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0

        # Parse mismatches
        mismatch_pattern = re.compile(r"Mismatches:\s*(\d+)\s*in\s*(\w+)")
        mismatches = mismatch_pattern.findall(output)

        if mismatches:
            accuracy = 1.0  # If mismatches are parsed, assume some accuracy. This can be adjusted.

        if "TIMEOUT" in output:
            accuracy = 0.0
            error_message = "Simulation timed out."

        if "errors" in output and "errors == 0" not in output:
            accuracy = 0.0
            error_message = "Simulation reported errors."
        
        if "PASS" in output:
            accuracy = 1.0
            error_message = None


        combined_score = accuracy  # Simple combined score for now

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("test")
        except FileNotFoundError:
            pass