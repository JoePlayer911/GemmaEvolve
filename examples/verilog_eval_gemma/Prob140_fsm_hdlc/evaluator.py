import os
import subprocess
import re
import tempfile
import logging

logger = logging.getLogger(__name__)

import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a reference model using Iverilog and VVP.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """

    try:
        # Create a temporary Verilog file for the candidate module
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run Iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "test", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run VVP
        vvp_cmd = ["vvp", "test"]
        vvp_result = subprocess.run(vvp_cmd, capture_output=True, text=True)

        # Parse the output for mismatches
        output = vvp_result.stdout
        mismatches = []
        match = re.search(r"Mismatches:\s*(\d+)\s*in\s*(\d+)", output)
        if match:
            mismatches = [int(match.group(1)), int(match.group(2))]
        
        # Check for FAIL or PASS keywords
        if "FAIL" in output:
            if mismatches:
                accuracy = 1.0 - (mismatches[0] / mismatches[1]) if mismatches[1] > 0 else 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            # If no FAIL or PASS, check for errors
            if "TIMEOUT" in output:
                accuracy = 0.0
            elif mismatches:
                accuracy = 1.0 - (mismatches[0] / mismatches[1]) if mismatches[1] > 0 else 0.0
            else:
                accuracy = 1.0

        # Calculate line count
        with open("candidate.sv", "r") as f:
            line_count = sum(1 for line in f)

        # Combine score (simple approach - can be enhanced)
        combined_score = accuracy * (line_count / 100) if line_count > 0 else accuracy

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": combined_score, "error": ""}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(["rm", "test"], check=False)
            subprocess.run(["rm", "candidate.sv"], check=False)
            subprocess.run(["rm", "test.map"], check=False)
        except:
            pass  # Ignore errors during cleanup


if __name__ == '__main__':
    # Example usage:
    candidate_code = """
    module example (
      input clk,
      input rst,
      input in,
      output reg out
    );

    always @(posedge clk) begin
      if (rst) begin
        out <= 0;
      end else begin
        out <= in;
      end
    end

    endmodule
    """

    result = evaluate(candidate_code)
    print(result)