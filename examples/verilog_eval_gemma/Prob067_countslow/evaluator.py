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
    Evaluates a Verilog module by simulating it against a reference module using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
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

        # Run the simulation using VVP
        simulation_result = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output to determine accuracy
        output = simulation_result.stdout
        line_count = len(code.splitlines())
        errors = 0
        clocks = 0
        
        if "FAIL" in output:
            accuracy = 0.0
            
            # Try to parse mismatch counts
            mismatches_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_pattern:
                errors = int(mismatches_pattern.group(1))
                clocks = int(mismatches_pattern.group(2))
            else:
                errors = 0
                clocks = 0
            
        elif "PASS" in output:
            accuracy = 1.0
            errors = 0
            clocks = 0
        else:
            # Parse mismatch counts from the output
            mismatches_pattern = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_pattern:
                errors = int(mismatches_pattern.group(1))
                clocks = int(mismatches_pattern.group(2))
            else:
                errors = 0
                clocks = 0
            
            if errors == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (float(errors) / clocks if clocks > 0 else 0.0)

        # Calculate the combined score (simple average of accuracy and line count)
        combined_score = (accuracy + (float(line_count) / 100)) / 2.0  # Normalize line count

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
            subprocess.run(["rm", "simulation"], check=False)
        except:
            pass