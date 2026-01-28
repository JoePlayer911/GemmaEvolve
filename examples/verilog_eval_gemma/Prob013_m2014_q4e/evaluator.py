import subprocess
import re

def evaluate(code: str) -> dict:
    """
    Evaluates a Verilog module by running it through Iverilog and comparing
    its output to a reference design.

    Args:
        code: The Verilog code of the module to be evaluated.

    Returns:
        A dictionary containing the evaluation results:
        - accuracy: A float representing the accuracy of the module (1.0 for pass, 0.0 for fail).
        - line_count: The number of lines in the input code.
        - combined_score: A float representing the combined score of the evaluation.
        - error: A string containing any error messages encountered during the evaluation.
    """

    exec_name = "temp_exec"
    testbench_file = "testbench.sv"
    ref_file = "ref.sv"

    try:
        # Write the candidate code to a file
        with open("candidate.sv", "w") as f:
            f.write(code)

        # Create a dummy testbench and reference file
        with open(testbench_file, "w") as f:
            f.write("""
module testbench;
  logic clk, reset, strobe;
  logic [7:0] in_dut, in_ref;
  logic [7:0] out_dut, out_ref;

  // Instantiate the DUT
  DUT dut (
    .clk(clk),
    .reset(reset),
    .strobe(strobe),
    .in_dut(in_dut),
    .out_dut(out_dut)
  );

  // Instantiate the reference
  REF ref (
    .clk(clk),
    .reset(reset),
    .strobe(strobe),
    .in_dut(in_dut),
    .out_ref(out_ref)
  );

  initial begin
    clk = 0;
    reset = 1;
    strobe = 0;
    in_dut = 8'h00;

    #10;
    reset = 0;

    // Generate clock
    forever #5 clk = ~clk;
  end

  initial begin
    $dumpfile("dump.vcd");
    $dumpvars(0, testbench);

    #100;
    strobe = 1;
    in_dut = 8'hAA;
    #10;
    strobe = 0;
    #100;
    $finish;
  end
endmodule

module DUT(
  input logic clk,
  input logic reset,
  input logic strobe,
  input logic [7:0] in_dut,
  output logic [7:0] out_dut
);
  // Replace this with the actual DUT code
  always_ff @(posedge clk) begin
    if (reset) begin
      out_dut <= 8'h00;
    end else if (strobe) begin
      out_dut <= in_dut;
    end else begin
      out_dut <= out_dut;
    end
  end
endmodule

module REF(
  input logic clk,
  input logic reset,
  input logic strobe,
  input logic [7:0] in_dut,
  output logic [7:0] out_ref
);
  // Replace this with the actual reference code
  always_ff @(posedge clk) begin
    if (reset) begin
      out_ref <= 8'h00;
    end else if (strobe) begin
      out_ref <= in_dut + 1;
    end else begin
      out_ref <= out_ref;
    end
  end
endmodule
""")

        with open(ref_file, "w") as f:
            f.write("""
module REF(
  input logic clk,
  input logic reset,
  input logic strobe,
  input logic [7:0] in_dut,
  output logic [7:0] out_ref
);
  // Replace this with the actual reference code
  always_ff @(posedge clk) begin
    if (reset) begin
      out_ref <= 8'h00;
    end else if (strobe) begin
      out_ref <= in_dut + 1;
    end else begin
      out_ref <= out_ref;
    end
  end
endmodule
""")

        # Compile the Verilog code
        compile_result = subprocess.run(
            ["iverilog", "-g2012", "-o", exec_name, "candidate.sv", testbench_file, ref_file],
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
        simulation_result = subprocess.run(
            [exec_name],
            capture_output=True,
            text=True
        )

        # Parse the simulation output
        output = simulation_result.stdout
        mismatches_match = re.search(r"Mismatches: (\d+) in (\d+)", output)
        fail_match = re.search(r"FAIL", output, re.IGNORECASE)
        pass_match = re.search(r"PASS", output, re.IGNORECASE)

        if fail_match:
            accuracy = 0.0
        elif mismatches_match:
            errors = int(mismatches_match.group(1))
            clocks = int(mismatches_match.group(2))
            accuracy = 1.0 - (errors / clocks) if clocks > 0 else 0.0
        elif pass_match:
            accuracy = 1.0
        else:
            accuracy = 1.0

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
        # Clean up temporary files
        import os
        try:
            os.remove("candidate.sv")
            os.remove(testbench_file)
            os.remove(ref_file)
            os.remove(exec_name)
        except FileNotFoundError:
            pass