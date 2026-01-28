import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference model.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results.
    """
    try:
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        simulation_cmd = ["vvp", "simulation"]
        simulation_result = subprocess.run(simulation_cmd, capture_output=True, text=True)

        # Parse the simulation output
        output = simulation_result.stdout
        line_count = len(output.splitlines())

        # Check for FAIL
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*X in\s*(\w+)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": line_count, "combined_score": 0.0, "error": "FAIL with mismatches"}
            else:
                return {"accuracy": 0.0, "line_count": line_count, "combined_score": 0.0, "error": "FAIL"}

        # Check for PASS or no errors
        if "PASS" in output or "errors" not in output:
            return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": None}
        else:
            # Parse mismatch counts
            mismatches_left = re.search(r"stats1\.errors_walk_left\s*=\s*(\d+)", output)
            mismatches_right = re.search(r"stats1\.errors_walk_right\s*=\s*(\d+)", output)
            total_mismatches = 0
            if mismatches_left:
                total_mismatches += int(mismatches_left.group(1))
            if mismatches_right:
                total_mismatches += int(mismatches_right.group(1))
            
            if total_mismatches > 0:
                accuracy = 1.0 - (total_mismatches / 1000)  # Normalize by assuming 1000 cycles
                return {"accuracy": max(0.0, accuracy), "line_count": line_count, "combined_score": accuracy, "error": f"Errors found: {total_mismatches}"}
            else:
                return {"accuracy": 1.0, "line_count": line_count, "combined_score": 1.0, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("simulation")
        except FileNotFoundError:
            pass