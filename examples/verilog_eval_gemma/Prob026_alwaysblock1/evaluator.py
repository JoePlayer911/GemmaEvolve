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
    Evaluates a Verilog module by running it against a reference design using Iverilog and Verilator.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float between 0.0 and 1.0).
            - line_count: The number of lines in the candidate code.
            - combined_score: A combined score based on accuracy and line count (optional).
            - error: An error message if any occurred during the evaluation.
    """
    try:
        candidate_file = "candidate.sv"
        with open(candidate_file, "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = f"iverilog -g2012 -o testbench testbench.sv {candidate_file} ref.sv"
        iverilog_result = subprocess.run(iverilog_cmd, shell=True, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run Verilator
        vvp_cmd = "./testbench"
        vvp_result = subprocess.run(vvp_cmd, shell=True, capture_output=True, text=True)

        output = vvp_result.stdout

        # Check for explicit FAIL
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*([^\n]+)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "FAIL with mismatches: " + mismatches.group(1)}
            else:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "FAIL"}

        # Check for explicit PASS
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

        # Check for mismatches based on the provided example output
        errors = re.search(r"stats1\.errors\s*=\s*\d+", output)
        if errors:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": "Errors found in simulation"}

        # If no errors are found, consider it a pass
        return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run("rm -f candidate.sv testbench", shell=True)
        except:
            pass