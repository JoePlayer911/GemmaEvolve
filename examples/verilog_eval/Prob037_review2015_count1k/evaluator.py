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
    Evaluates a Verilog module using iverilog and vvp.

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
            ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr.strip()
            }

        # Run the simulation
        simulation_result = subprocess.run(
            ["vvp", "test"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        
        if "FAIL" in output:
            accuracy = 0.0
            
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                if clocks > 0:
                    accuracy = (1.0 - (errors / clocks)) if errors < clocks else 0.0
                else:
                    accuracy = 0.0
            
            return {
                "accuracy": accuracy,
                "line_count": len(code.splitlines()),
                "combined_score": accuracy,
                "error": ""
            }

        if "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                if clocks > 0:
                    accuracy = (1.0 - (errors / clocks)) if errors < clocks else 0.0
                else:
                    accuracy = 1.0 # Assume pass if clocks is zero and no errors are found
            else:
                accuracy = 1.0  # Assume pass if no mismatches found and no PASS/FAIL

        return {
            "accuracy": accuracy,
            "line_count": len(code.splitlines()),
            "combined_score": accuracy,
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
            subprocess.run(["rm", "candidate.sv"], capture_output=True)
            subprocess.run(["rm", "test"], capture_output=True)
        except:
            pass