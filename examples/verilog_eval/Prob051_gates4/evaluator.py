import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: accuracy, line_count, combined_score, error.
    """
    try:
        # Write the candidate module to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "exec", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = ["vvp", "exec"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        line_count = len(output.splitlines())

        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches:
                x = int(mismatches.group(1))
                y = int(mismatches.group(2))
                accuracy = 1.0 - (float(x) / y)
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Check for error counts
            error_counts = re.search(r"stats1\.errors\s*=\s*(\d+)", output)
            if error_counts:
                errors = int(error_counts.group(1))
                if errors == 0:
                    accuracy = 1.0
                else:
                    accuracy = 0.0
            else:
                accuracy = 1.0

        combined_score = accuracy  # Simplified for now. Can be customized.

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("exec")
        except FileNotFoundError:
            pass