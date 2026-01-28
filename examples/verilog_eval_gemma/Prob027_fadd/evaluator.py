import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a reference design.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary containing the evaluation results.
    """
    try:
        # Write the candidate module to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = f"iverilog -g2012 -o test { 'candidate.sv' } testbench.sv ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_cmd = f"vvp test"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)
        output = vvp_result.stdout

        # Check for FAIL
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (.*)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"FAIL with mismatches: {mismatches.group(1)}"}
            else:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "FAIL"}

        # Check for PASS or no errors
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": None}

        # Parse mismatch counts from the output
        mismatches = re.search(r"Mismatches: (.*)", output)
        if mismatches:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"Mismatches found: {mismatches.group(1)}"}
        
        # If no errors are found, assume PASS
        return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up generated files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("test")
        except FileNotFoundError:
            pass