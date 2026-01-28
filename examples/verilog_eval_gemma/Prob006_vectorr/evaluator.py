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
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test_exec", "candidate.sv", "testbench.sv", "ref.sv"],
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
        simulation_result = subprocess.run(
            ["vvp", "test_exec"],
            capture_output=True,
            text=True
        )

        output = simulation_result.stdout
        
        # Check for "FAIL"
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                errors = int(mismatches.group(1))
                total_samples = int(mismatches.group(2))
                accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
                return {
                    "accuracy": accuracy,
                    "line_count": len(code.splitlines()),
                    "combined_score": accuracy,
                    "error": ""
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": len(code.splitlines()),
                    "combined_score": 0.0,
                    "error": ""
                }
        
        # Check for "PASS"
        if "PASS" in output:
            return {
                "accuracy": 1.0,
                "line_count": len(code.splitlines()),
                "combined_score": 1.0,
                "error": ""
            }

        # Parse mismatch counts from the output
        mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches:
            errors = int(mismatches.group(1))
            total_samples = int(mismatches.group(2))
            accuracy = 1.0 - (errors / total_samples) if total_samples > 0 else 0.0
            return {
                "accuracy": accuracy,
                "line_count": len(code.splitlines()),
                "combined_score": accuracy,
                "error": ""
            }

        # If no errors are found
        return {
            "accuracy": 1.0,
            "line_count": len(code.splitlines()),
            "combined_score": 1.0,
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
            subprocess.run(["rm", "test_exec"], check=False)
        except:
            pass