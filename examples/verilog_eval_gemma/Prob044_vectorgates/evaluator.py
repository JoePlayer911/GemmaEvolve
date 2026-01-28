import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Create a temporary Verilog file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "sim", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )
        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        sim_result = subprocess.run(
            ["vvp", "sim"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = sim_result.stdout
        line_count = len(output.splitlines())

        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0
            
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts
            mismatches_match = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
            if mismatches_match:
                mismatches = int(mismatches_match.group(1))
                total = int(mismatches_match.group(2))
                accuracy = 1.0 - (float(mismatches) / float(total)) if total > 0 else 1.0
            
            # Check for errors reported by the testbench
            error_match = re.search(r"stats1\.errors\s*=\s*(\d+)", output)
            if error_match:
                errors = int(error_match.group(1))
                if errors > 0:
                    accuracy = min(1.0, 1.0 - (float(errors) / 100.0)) # Scale errors to a reasonable accuracy impact

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("sim")
        except FileNotFoundError:
            pass