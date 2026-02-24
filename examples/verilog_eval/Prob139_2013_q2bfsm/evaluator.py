import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by simulating it against a reference design.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
            - accuracy: The accuracy score (float).
            - line_count: The number of lines in the candidate code (int).
            - combined_score: A combined score based on accuracy and line count (float).
            - error: An error message if any occurred during the process (str), otherwise None.
    """
    try:
        # Write the candidate code to a temporary file
        candidate_file = "candidate.sv"
        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_command = f"iverilog -g2012 -o test candidate.sv testbench.sv ref.sv"
        compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"Compilation error: {compile_result.stderr}"}

        # Run the simulation
        simulation_command = "./test"
        simulation_result = subprocess.run(simulation_command, shell=True, capture_output=True, text=True)

        # Parse the simulation output
        output = simulation_result.stdout
        
        # Check for FAIL
        if "FAIL" in output:
            mismatches = re.search(r"Mismatches:\s*X in\s*(\w+)", output)
            if mismatches:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": f"FAIL detected with mismatches in {mismatches.group(1)}"}
            else:
                return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": "FAIL detected with no mismatches parsed"}

        # Check for PASS or errors
        if "PASS" in output:
            accuracy = 1.0
        else:
            # Parse mismatch counts
            mismatches = re.search(r"errors\s*:\s*(\d+)", output)
            if mismatches:
                error_count = int(mismatches.group(1))
                accuracy = 1.0 - (error_count / 1000.0)  # Example: Assume max 1000 cycles
            else:
                accuracy = 1.0

        # Calculate line count
        line_count = len(code.splitlines())

        # Calculate combined score (example: accuracy weighted more heavily)
        combined_score = 0.8 * accuracy + 0.2 * (1.0 - (line_count / 1000.0))  # Normalize line count

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove(candidate_file)
            os.remove("test")
        except FileNotFoundError:
            pass