`timescale 1ns / 1ps

module testbench;

  reg [31:0] in;
  wire [31:0] out;
  
  // Instantiate the Unit Under Test (UUT)
  TopModule uut (
    .in(in), 
    .out(out)
  );

  integer i;
  integer correct_count;
  integer total_tests;
  reg [31:0] expected;

  // Function to calculate expected byte reversal
  function [31:0] calc_reversal;
    input [31:0] val;
    begin
      calc_reversal = {val[7:0], val[15:8], val[23:16], val[31:24]};
    end
  endfunction

  initial begin
    `ifdef DUMP_WAVEFORM
      $dumpfile("waveform.vcd");
      $dumpvars(0, testbench);
    `endif

    correct_count = 0;
    total_tests = 100;

    // Test specific cases
    in = 32'h12345678; #10;
    expected = calc_reversal(in);
    check_result();

    in = 32'h00000000; #10;
    expected = calc_reversal(in);
    check_result();

    in = 32'hFFFFFFFF; #10;
    expected = calc_reversal(in);
    check_result();

    // Random tests
    for (i = 0; i < total_tests - 3; i = i + 1) begin
      in = $random;
      #10;
      expected = calc_reversal(in);
      check_result();
    end

    // Print final summary for evaluator parsing
    $display("SUMMARY: Passed %0d/%0d tests", correct_count, total_tests);
    
    if (correct_count == total_tests)
      $display("RESULT: PASS");
    else
      $display("RESULT: FAIL");

    $finish;
  end

  task check_result;
    begin
      if (out === expected) begin
        correct_count = correct_count + 1;
      end else begin
        $display("ERROR: in=%h, out=%d, expected=%h", in, out, expected);
      end
    end
  endtask

endmodule
