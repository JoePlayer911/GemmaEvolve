import os
import subprocess
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench and analyzing the output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float).
            - line_count: The number of lines in the Verilog code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message if any occurred during evaluation (str).
    """
    try:
        exec_name = "eval_temp"
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = f"iverilog -g2012 -o {exec_name} candidate.sv testbench.sv ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"Iverilog error: {iverilog_result.stderr}"}

        # Run vvp
        vvp_cmd = f"{exec_name} -v"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        output = vvp_result.stdout

        # Parse the output for mismatches
        mismatch_pattern = re.compile(r"Mismatches:\s*([a-zA-Z]+)\s*in\s*([a-zA-Z]+)")
        mismatches = []
        for match in mismatch_pattern.finditer(output):
            mismatches.append((match.group(1), match.group(2)))

        # Check for explicit FAIL or PASS
        if "FAIL" in output:
            if mismatches:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # If no explicit PASS/FAIL and no mismatches found, assume PASS
            if "errors" not in output and "TIMEOUT" not in output:
                accuracy = 1.0
            else:
                accuracy = 0.0 # Assume failure if errors or timeout present.

        # Calculate line count
        line_count = len(code.splitlines())

        # Calculate combined score
        combined_score = accuracy * (1.0 / line_count) if line_count > 0 else 0.0

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(f"rm -f {exec_name}", shell=True)
            subprocess.run(f"rm -f candidate.sv", shell=True)
        except:
            pass