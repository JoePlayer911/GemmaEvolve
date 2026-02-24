import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through Iverilog and comparing the output
    to a reference testbench.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results, including accuracy,
              line count, combined score, and any error messages.
    """
    try:
        # Create a temporary file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code using Iverilog
        compile_process = subprocess.run(
            ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_process.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_process.stderr
            }

        # Run the simulation using VVP
        simulation_process = subprocess.run(
            ["vvp", "simulation"],
            capture_output=True,
            text=True
        )

        output = simulation_process.stdout
        
        # Check for "FAIL" and set accuracy to 0.0 if found, unless mismatches are parsed.
        if "FAIL" in output:
            errors = 0
            clocks = 0

            # Attempt to parse mismatch counts
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))

            if errors == 0 and clocks == 0:
                accuracy = 0.0
            else:
                accuracy = 0.0
        else:
            # Check for "PASS" or if no errors are found, set accuracy to 1.0
            if "PASS" in output:
                accuracy = 1.0
            else:
                # Parse mismatch counts to determine accuracy
                errors = 0
                clocks = 0
                match = re.search(r"Mismatches: (\d+) in (\d+)", output)
                if match:
                    errors = int(match.group(1))
                    clocks = int(match.group(2))
                
                if errors == 0 and clocks == 0:
                    accuracy = 1.0
                else:
                    accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 1.0

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
        import os
        try:
            os.remove("candidate.sv")
            os.remove("simulation")
        except FileNotFoundError:
            pass