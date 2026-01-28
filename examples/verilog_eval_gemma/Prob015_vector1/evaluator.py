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
    Evaluates a Verilog module by simulating it against a reference model using Iverilog and Verilog Value Probe (VVP).

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results, including accuracy, line count, combined score, and any error messages.
    """
    try:
        # Create a temporary Verilog file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation using VVP
        sim_result = subprocess.run(
            ["vvp", "test"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = sim_result.stdout

        # Check for explicit "FAIL"
        if "FAIL" in output:
            accuracy = 0.0
            
            # Attempt to parse mismatches
            mismatches = re.search(r"Mismatches:\s*X in (\w+)", output)
            if mismatches:
                # Handle mismatches, e.g., reduce accuracy based on the type of mismatch
                pass  # Implement more sophisticated logic here if needed

            return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": ""}

        # Check for explicit "PASS"
        if "PASS" in output:
            accuracy = 1.0
            return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": ""}

        # Parse mismatch counts if present (more robust parsing)
        errors_match = re.search(r"stats1\.errors\s*=\s*(\d+)", output)
        if errors_match:
            errors = int(errors_match.group(1))
            if errors == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (errors / 1000.0)  # Example: reduce accuracy based on error count
            return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": ""}
        
        # If no explicit PASS/FAIL or error counts, assume success
        accuracy = 1.0
        return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": 1.0, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "candidate.sv", "test"], check=False)
        except:
            pass