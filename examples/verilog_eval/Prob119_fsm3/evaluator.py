import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through Iverilog and comparing
    the output to a reference design.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results.
    """
    try:
        # Create a temporary Verilog file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog to compile the candidate module and the testbench
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run the simulation
        simulation_cmd = ["vvp", "simulation"]
        simulation_result = subprocess.run(simulation_cmd, capture_output=True, text=True)

        # Parse the simulation output to determine accuracy
        output = simulation_result.stdout
        
        if "FAIL" in output:
            accuracy = 0.0
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = 1.0 - (errors / clocks if clocks > 0 else 0.0)
            
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Attempt to parse mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = 1.0 - (errors / clocks if clocks > 0 else 0.0)
            else:
                accuracy = 1.0

        # Count the lines in the candidate module
        line_count = len(code.splitlines())

        # Combine accuracy and line count into a single score (example)
        combined_score = accuracy * (line_count / 100.0) if line_count < 100 else accuracy

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": None}

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