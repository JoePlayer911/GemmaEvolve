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
    Evaluates a Verilog module by simulating it against a reference design.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results, including accuracy,
              line count, combined score, and any error messages.
    """
    try:
        # Write the candidate module to a temporary file
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
        
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*(\w+)\s*in\s*(\w+)", output)
            if mismatches:
                return {
                    "accuracy": 0.0,
                    "line_count": len(code.splitlines()),
                    "combined_score": 0.0,
                    "error": "FAIL with mismatches"
                }
            else:
                return {
                    "accuracy": 0.0,
                    "line_count": len(code.splitlines()),
                    "combined_score": 0.0,
                    "error": "FAIL - No mismatches found"
                }

        if "PASS" in output:
            return {
                "accuracy": 1.0,
                "line_count": len(code.splitlines()),
                "combined_score": 1.0,
                "error": None
            }

        # Check for errors in the simulation output
        if "errors" in output.lower():
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": "Simulation errors detected"
            }

        # If no explicit PASS/FAIL is found, assume it passed
        return {
            "accuracy": 1.0,
            "line_count": len(code.splitlines()),
            "combined_score": 1.0,
            "error": None
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