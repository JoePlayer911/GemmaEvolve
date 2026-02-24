import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench and analyzing the output.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results.
        Keys: 'accuracy', 'line_count', 'combined_score', 'error'
    """

    try:
        # Write the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog to compile the module and testbench
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        simulation_result = subprocess.run(["vvp", "simulation"], capture_output=True, text=True)

        # Analyze the simulation output
        output = simulation_result.stdout
        accuracy = 1.0
        errors = 0
        mismatches = 0

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Parse mismatch counts from the output
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                mismatches = int(match.group(2))
            
            if errors > 0:
                accuracy = 1.0 - (float(errors) / mismatches) if mismatches > 0 else 0.0
            
            if "PASS" in output and errors == 0:
                accuracy = 1.0
            
        line_count = len(code.splitlines())
        combined_score = accuracy  # Simple combined score, can be modified
        error = ""

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": error}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("simulation")
        except FileNotFoundError:
            pass  # Ignore if files don't exist