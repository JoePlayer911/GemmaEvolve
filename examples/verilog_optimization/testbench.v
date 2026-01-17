`timescale 1ns / 1ps

module testbench;

  reg [15:0] in;
  wire [4:0] out;
  
  // Instantiate the Unit Under Test (UUT)
  popcount16 uut (
    .in(in), 
    .out(out)
  );

  integer i;
  integer correct_count;
  integer total_tests;
  reg [4:0] expected;
  integer j;

  // Function to calculate expected popcount
  function [4:0] calc_popcount;
    input [15:0] val;
    integer k;
    begin
      calc_popcount = 0;
      for (k = 0; k < 16; k = k + 1) begin
        if (val[k]) calc_popcount = calc_popcount + 1;
      end
    end
  endfunction

  initial begin
    $dumpfile("waveform.vcd");
    $dumpvars(0, testbench);

    correct_count = 0;
    total_tests = 100;

    // Test specific cases
    in = 16'h0000; #10;
    expected = calc_popcount(in);
    check_result();

    in = 16'hFFFF; #10;
    expected = calc_popcount(in);
    check_result();

    in = 16'hAAAA; #10;
    expected = calc_popcount(in);
    check_result();

    in = 16'h5555; #10;
    expected = calc_popcount(in);
    check_result();

    // Random tests
    for (i = 0; i < total_tests - 4; i = i + 1) begin
      in = $random;
      #10;
      expected = calc_popcount(in);
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
        $display("ERROR: in=%h, out=%d, expected=%d", in, out, expected);
      end
    end
  endtask

endmodule
