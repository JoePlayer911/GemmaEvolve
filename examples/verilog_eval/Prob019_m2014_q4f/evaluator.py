import os
import subprocess
import re
import tempfile

def evaluate(code: str) -> dict:
    # Write code to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.v', prefix='verilog_', delete=False) as f:
        f.write(code)
        candidate_path = f.name

    executable_path = candidate_path + ".out"
    testbench_path = "testbench.sv"
    ref_path = "ref.sv" # specific to this problem

    try:
        # Compile
        compile_cmd = ["iverilog", "-g2012", "-o", executable_path, candidate_path, testbench_path, ref_path]
        subprocess.check_output(compile_cmd, stderr=subprocess.STDOUT, timeout=10)

        # Run
        run_cmd = ["vvp", executable_path]
        output = subprocess.check_output(run_cmd, stderr=subprocess.STDOUT, timeout=10).decode()

        # Parse Output (Example Logic)
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
        else:
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