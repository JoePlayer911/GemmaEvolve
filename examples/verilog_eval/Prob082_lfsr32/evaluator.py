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
    Evaluates a Verilog module by simulating it against a reference model using Iverilog and VVP.
    """
    try:
        exec_name = "a.out"  # Temporary executable name
        testbench_file = "testbench.sv"
        ref_file = "ref.sv"

        # Write the candidate code to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Compile the Verilog code
        compile_cmd = f"iverilog -g2012 -o {exec_name} candidate.sv {testbench_file} {ref_file}"
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, shell=True)

        if compile_result.returncode != 0:
            return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": compile_result.stderr}

        # Run the simulation
        sim_result = subprocess.run(f"./{exec_name}", capture_output=True, text=True, shell=True)

        # Parse the simulation output
        output = sim_result.stdout
        line_count = len(output.splitlines())

        accuracy = 1.0
        error_message = None

        if "FAIL" in output:
            accuracy = 0.0
        else:
            # Parse mismatch counts
            mismatch_pattern = re.compile(r"Mismatches:\s*(\d+)\s*in\s*(\d+)")
            match = mismatch_pattern.search(output)
            if match:
                errors = int(match.group(1))
                clocks = int(match.group(2))
                if errors > 0:
                    accuracy = 1.0 - (float(errors) / clocks) if clocks > 0 else 0.0
            else:
                # Check for errors_q
                errors_q_pattern = re.compile(r"stats\.errors_q = (\d+)")
                match_q = errors_q_pattern.search(output)
                if match_q:
                    errors_q = int(match_q.group(1))
                    if errors_q > 0:
                        accuracy = 1.0 - (float(errors_q) / 1) # Assuming 1 clock cycle

        if "TIMEOUT" in output:
            accuracy = 0.0
            error_message = "Simulation timed out."

        return {"accuracy": accuracy, "line_count": line_count, "combined_score": accuracy, "error": error_message}

    except Exception as e:
        return {"accuracy": 0.0, "line_count": 0, "combined_score": 0.0, "error": str(e)}
    finally:
        # Clean up temporary files
        try:
            subprocess.run(f"rm -f candidate.sv {exec_name}", shell=True, check=False, capture_output=True)
        except:
            pass #Ignore cleanup errors

if __name__ == '__main__':
    # Example usage:
    verilog_code = """
    module dut (
        input clk,
        input rst,
        input [7:0] in,
        output reg [7:0] out
    );

    always @(posedge clk) begin
        if (rst) begin
            out <= 0;
        end else begin
            out <= in + 1;
        end
    end

    endmodule
    """

    ref_code = """
    module ref (
        input clk,
        input rst,
        input [7:0] in,
        output [7:0] out
    );

    always @(posedge clk) begin
        if (rst) begin
            out <= 0;
        end else begin
            out <= in + 1;
        end
    end

    endmodule
    """

    # Create dummy testbench.sv and ref.sv files
    with open("testbench.sv", "w") as f:
        f.write("""
module testbench;
  reg clk, rst;
  reg [7:0] in;
  wire [7:0] out;

  dut dut_inst (
    .clk(clk),
    .rst(rst),
    .in(in),
    .out(out)
  );

  initial begin
    clk = 0;
    rst = 1;
    in = 0;
    #10 rst = 0;
    #10 in = 8'd5;
    #10 $finish;
  end

  always #5 clk = ~clk;
endmodule
""")

    with open("ref.sv", "w") as f:
        f.write(ref_code)


    result = evaluate(verilog_code)
    print(result)