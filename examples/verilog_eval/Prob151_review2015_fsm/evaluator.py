import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module using iverilog and vvp.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        exec_name = "a.out"
        candidate_name = "candidate.sv"
        with open(candidate_name, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_command = f"iverilog -g2012 -o {exec_name} {candidate_name} testbench.sv ref.sv"
        compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        simulation_result = subprocess.run(f"./{exec_name}", shell=True, capture_output=True, text=True)

        output = simulation_result.stdout
        error = simulation_result.stderr

        # Check for FAIL
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches:
                x = int(mismatches.group(1))
                y = int(mismatches.group(2))
                accuracy = 1.0 - (float(x) / y) if y > 0 else 0.0
                return {"accuracy": accuracy, "line_count": 0, "combined_score": accuracy, "error": ""}

            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": ""}

        # Check for PASS or mismatches
        if "PASS" in output:
            return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": ""}

        # Parse mismatches from output
        mismatches = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches:
            x = int(mismatches.group(1))
            y = int(mismatches.group(2))
            accuracy = 1.0 - (float(x) / y) if y > 0 else 0.0
            return {"accuracy": accuracy, "line_count": 0, "combined_score": accuracy, "error": ""}

        # If no errors are found, assume PASS
        return {"accuracy": 1.0, "line_count": 0, "combined_score": 1.0, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up the generated files
        import os
        try:
            os.remove(candidate_name)
            os.remove(exec_name)
        except FileNotFoundError:
            pass