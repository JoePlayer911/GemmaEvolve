import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through iverilog and vvp.

    Args:
        code: The Verilog code to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary Verilog file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "exec", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = ["vvp", "exec"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output for mismatches
        output = vvp_result.stdout
        errors = 0
        clocks = 0
        error_time = None
        error_time_q = None

        match_errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if match_errors:
            errors = int(match_errors.group(1))
            clocks = int(match_errors.group(2))

        match_errors_q = re.search(r"errors_q = (\d+)", output)
        if match_errors_q:
            errors_q = int(match_errors_q.group(1))
            
        if "FAIL" in output:
            if errors > 0 or errors_q > 0:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            if errors == 0 and errors_q == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (errors + errors_q) / (clocks if clocks > 0 else 1)  # Penalize for mismatches

        # Calculate combined score
        combined_score = accuracy

        return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": combined_score, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("exec")
        except FileNotFoundError:
            pass