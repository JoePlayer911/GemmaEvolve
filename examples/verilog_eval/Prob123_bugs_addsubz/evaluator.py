import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Save the candidate code to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = ["vvp", "test"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output for mismatches or failures
        output = vvp_result.stdout
        accuracy = 1.0
        mismatches = 0

        if "FAIL" in output:
            accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\w+)", output)
            if match:
                mismatches = int(match.group(1))
                # Adjust accuracy based on mismatches (example: linear decrease)
                accuracy = max(0.0, 1.0 - (mismatches / 100.0))  # Assuming a maximum of 100 mismatches

        # Get line count of the candidate code
        line_count = len(code.splitlines())

        # Combined score (example: accuracy * line_count)
        combined_score = accuracy * line_count

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": None}

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