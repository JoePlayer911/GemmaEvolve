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
    Evaluates a Verilog module by running it through Iverilog and comparing its output
    against a reference model.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "eval_exec", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        vvp_cmd = ["vvp", "eval_exec"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output for mismatches
        output = vvp_result.stdout
        errors = 0
        clocks = 0
        errors_z = 0
        
        mismatch_pattern = re.compile(r"Mismatches: (\d+) in (\d+)")
        match = mismatch_pattern.search(output)

        if match:
            errors = int(match.group(1))
            clocks = int(match.group(2))
        
        # Check for FAIL or PASS
        if "FAIL" in output:
            if errors > 0:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            if errors == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0

        # Calculate the combined score (simple accuracy for now)
        combined_score = accuracy

        return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "eval_exec"], check=False)
            subprocess.run(["rm", "testbench.o"], check=False)
            subprocess.run(["rm", "ref.o"], check=False)
            subprocess.run(["rm", "core"], check=False)
        except:
            pass