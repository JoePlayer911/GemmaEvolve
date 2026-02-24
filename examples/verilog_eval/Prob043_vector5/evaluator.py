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
    Evaluates a Verilog module by running it through Iverilog and comparing the output
    to a reference design.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results.  Keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        vvp_cmd = ["vvp", "test"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output
        output = vvp_result.stdout
        
        # Check for explicit FAIL
        if "FAIL" in output:
            errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if errors:
                mismatches = int(errors.group(1))
                total_samples = int(errors.group(2))
                accuracy = 1.0 - (mismatches / total_samples) if total_samples > 0 else 0.0
                return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": None}
            else:
                return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": None}
            
        # Check for explicit PASS
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

        # Parse mismatch counts
        errors = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if errors:
            mismatches = int(errors.group(1))
            total_samples = int(errors.group(2))
            accuracy = 1.0 - (mismatches / total_samples) if total_samples > 0 else 0.0
            return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": None}
        else:
            return {"accuracy": 1.0, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test"], check=False)
        except:
            pass