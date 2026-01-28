import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module using iverilog and vvp.

    Args:
        code: The Verilog code to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        executable_name = "a.out"  # Default executable name
        candidate_file = "candidate.sv"
        testbench_file = "testbench.sv"
        ref_file = "ref.sv"

        # Write the candidate code to a file
        with open(candidate_file, "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_cmd = ["iverilog", "-g2012", "-o", executable_name, candidate_file, testbench_file, ref_file]
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        simulation_cmd = [executable_name]
        simulation_result = subprocess.run(simulation_cmd, capture_output=True, text=True)

        # Parse the simulation output to determine accuracy
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            accuracy = 0.0
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
            return {"accuracy": accuracy, "line_count": line_count, "combined_score": 0.0, "error": ""}

        if "PASS" in output:
            accuracy = 1.0
        else:
            mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if mismatches_match:
                errors = int(mismatches_match.group(1))
                clocks = int(mismatches_match.group(2))
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 1.0
            else:
                accuracy = 1.0

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up files
        import os
        try:
            os.remove(candidate_file)
            os.remove(executable_name)
        except FileNotFoundError:
            pass