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
    Evaluates a Verilog module using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: accuracy, line_count, combined_score, error.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_process = subprocess.run(
            ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )
        if compile_process.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_process.stderr}

        # Run the simulation
        simulation_process = subprocess.run(
            ["vvp", "test"],
            capture_output=True,
            text=True
        )

        output = simulation_process.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
                return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": None}
            else:
                return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": None}
        
        # Parse mismatch counts
        mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches:
            errors = int(mismatches.group(1))
            total_samples = int(mismatches.group(2))
            accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
        else:
            # Check for PASS
            if "PASS" in output:
                accuracy = 1.0
            else:
                # Assume PASS if no mismatches and no FAIL
                accuracy = 1.0

        return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test"], check=False)
        except:
            pass