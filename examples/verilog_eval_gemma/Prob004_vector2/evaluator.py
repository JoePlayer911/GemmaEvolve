import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through Iverilog and comparing
    its output to a reference design.

    Args:
        code (str): The Verilog code of the module to be evaluated.

    Returns:
        dict: A dictionary containing the evaluation results.
              Keys: 'accuracy', 'line_count', 'combined_score', 'error'
    """
    try:
        # Write the candidate code to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", "sim", "candidate.sv", "testbench.sv", "ref.sv"],
            capture_output=True,
            text=True
        )

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        sim_result = subprocess.run(
            ["vvp", "sim"],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = sim_result.stdout
        accuracy = 1.0
        errors = 0
        clocks = 0
        errors_out = 0

        if "FAIL" in output:
            accuracy = 0.0

        # Parse mismatch counts
        mismatch_pattern = re.compile(r"Mismatches: (\d+) in (\d+)")
        match = mismatch_pattern.search(output)
        if match:
            errors = int(match.group(1))
            clocks = int(match.group(2))

        if "PASS" in output:
            accuracy = 1.0
        elif errors > 0:
            accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0


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
        # Clean up the generated files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("sim")
        except FileNotFoundError:
            pass