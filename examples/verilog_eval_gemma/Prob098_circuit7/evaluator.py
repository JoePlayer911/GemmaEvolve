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
        executable_name = "temp_exec"  # Temporary executable name
        testbench_file = "testbench.sv"
        reference_file = "ref.sv"

        # Write the code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_command = f"iverilog -g2012 -o {executable_name} candidate.sv {testbench_file} {reference_file}"
        compile_result = subprocess.run(compile_command, shell=True, capture_output=True, text=True)

        if compile_result.returncode != 0:
            return {
                "accuracy": 0.0,
                "line_count": len(code.splitlines()),
                "combined_score": 0.0,
                "error": compile_result.stderr
            }

        # Run the simulation
        simulation_result = subprocess.run(f"./{executable_name}", shell=True, capture_output=True, text=True)

        # Parse the simulation output to determine accuracy
        output = simulation_result.stdout
        line_count = len(code.splitlines())

        if "FAIL" in output:
            accuracy = 0.0
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = (clocks - errors) / clocks if clocks > 0 else 0.0
            return {
                "accuracy": accuracy,
                "line_count": line_count,
                "combined_score": accuracy,
                "error": ""
            }
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # Check for mismatch counts
            mismatch_pattern = r"Mismatches: (\d+) in (\d+)"
            match = re.search(mismatch_pattern, output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                accuracy = (clocks - errors) / clocks if clocks > 0 else 0.0
            else:
                accuracy = 1.0

        return {
            "accuracy": accuracy,
            "line_count": line_count,
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
            os.remove(executable_name)
        except FileNotFoundError:
            pass