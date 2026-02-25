import os
import subprocess
import re
import tempfile

# Resolve testbench/ref paths relative to THIS file, not the working directory.
# This is critical because OpenEvolve worker processes run from the project root.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def evaluate(code: str) -> dict:
    # OpenEvolve passes a FILE PATH, not code content.
    # If the input is a file path, read the code from it.
    if os.path.exists(code) and os.path.isfile(code):
        with open(code, 'r') as f:
            code = f.read()

    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', prefix='verilog_', delete=False) as f:
        f.write(code)
        candidate_path = f.name

    executable_path = candidate_path + ".out"
    testbench_path = os.path.join(_SCRIPT_DIR, "testbench.sv")
    ref_path = os.path.join(_SCRIPT_DIR, "ref.sv")

    try:
        # Compile
        compile_cmd = ["iverilog", "-g2012", "-o", executable_path, candidate_path, testbench_path, ref_path]
        try:
            subprocess.check_output(compile_cmd, stderr=subprocess.STDOUT, timeout=10)
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode() if e.output else "Unknown compilation error"
            line_count = len(code.strip().splitlines())
            # Partial credit: give evolution a gradient even on compile failure
            partial_score = 0.0
            if line_count > 0 and "module" in code.lower():
                partial_score = 0.05  # Has valid-looking Verilog structure
            if "TopModule" in code:
                partial_score = 0.1   # Correct module name
            return {
                "accuracy": 0.0,
                "line_count": line_count,
                "combined_score": partial_score,
                "error": f"Compilation failed:\n{error_msg}"
            }

        # Run
        run_cmd = ["vvp", executable_path]
        try:
            output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, timeout=10).decode()
        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode() if e.output else "Unknown runtime error"
            return {
                "accuracy": 0.0,
                "line_count": len(code.strip().splitlines()),
                "combined_score": 0.15,  # Compiled but runtime error
                "error": f"Runtime error:\n{error_msg}"
            }

        # Parse Output
        accuracy = 0.0
        if "PASS" in output:
            accuracy = 1.0
        elif "Mismatches:" in output:
            # Parse specific counts if available
            match = re.search(r"Mismatches: (\d+) in (\d+)", output)
            if match:
                errors = int(match.group(1))
                total = int(match.group(2))
                accuracy = 1.0 - (errors / total)
        elif "TIMEOUT" in output:
            accuracy = 0.0

        # Calculate Score
        line_count = len(code.strip().splitlines())
        combined_score = accuracy
        # bonus for conciseness only if correct
        if accuracy == 1.0:
            combined_score += max(0, (100 - line_count) / 1000.0)

        return {
            "accuracy": accuracy,
            "line_count": line_count,
            "combined_score": combined_score,
            "error": None
        }
    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        if os.path.exists(candidate_path):
            os.remove(candidate_path)
        if os.path.exists(executable_path):
            os.remove(executable_path)
