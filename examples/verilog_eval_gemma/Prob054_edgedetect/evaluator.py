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
    Evaluates a Verilog module by simulating it against a reference module.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "sim", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        sim_result = subprocess.run(
            ["vvp", "sim"],
            capture_output=True,
            text=True
        )

        output = sim_result.stdout

        # Parse the output for mismatches
        mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
        match = re.search(mismatch_pattern, output)
        errors = 0
        clocks = 0
        if match:
            errors = int(match.group(1))
            clocks = int(match.group(2))
        
        # Check for "FAIL" or "PASS"
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
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0

        # Calculate line count
        line_count = len(code.splitlines())

        # Calculate combined score (simple accuracy for now)
        combined_score = accuracy

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": ""
        }

    except Exception as e:
        return {
            "accuracy": 0.0,
            "line_count": len(code.splitlines()),
            "combined_score": 0.0,
            "error": str(e)
        }
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "sim"], check=False)
        except:
            pass