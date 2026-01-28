import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it against a testbench.

    Args:
        code: The Verilog code of the module to evaluate.

    Returns:
        A dictionary with keys: 'accuracy', 'line_count', 'combined_score', 'error'.
    """
    try:
        # Save the candidate code to a temporary file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Run iverilog
        iverilog_cmd = ["iverilog", "-g2012", "-o", "simulation", "candidate.sv", "testbench.sv", "ref.sv"]
        iverilog_result = subprocess.run(iverilog_cmd, capture_output=True, text=True)

        if iverilog_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": iverilog_result.stderr}

        # Run vvp
        vvp_result = subprocess.run(["vvp", "simulation"], capture_output=True, text=True)

        # Parse the output for mismatches
        output = vvp_result.stdout
        errors = 0
        clocks = 0
        error_time = None
        error_time_q = None

        mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
        if mismatches_match:
            errors = int(mismatches_match.group(1))
            clocks = int(mismatches_match.group(2))
        
        error_time_match = re.search(r"stats1\.errortime = (\d+)", output)
        if error_time_match:
            error_time = int(error_time_match.group(1))
        
        error_time_q_match = re.search(r"stats1\.errortime_q = (\d+)", output)
        if error_time_q_match:
            error_time_q = int(error_time_q_match.group(1))

        # Check for "FAIL" or "PASS"
        if "FAIL" in output:
            if errors > 0:
                accuracy = 0.0
            else:
                accuracy = 0.0
        elif "PASS" in output:
            accuracy = 1.0
        else:
            if errors == 0:
                accuracy = 1.0
            else:
                accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0

        return {"accuracy": accuracy, "line_count": len(code.splitlines()), "combined_score": accuracy, "error": None}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": len(code.splitlines()), "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove("simulation")
        except FileNotFoundError:
            pass

if __name__ == '__main__':
    # Example Usage:
    verilog_code = """
    module adder (
        input clk,
        input rst,
        input [7:0] a,
        input [7:0] b,
        output reg [7:0] sum
    );

    always @(posedge clk) begin
        if (rst) begin
            sum <= 0;
        end else begin
            sum <= a + b;
        end
    end

    endmodule
    """
    
    result = evaluate(verilog_code)
    print(result)