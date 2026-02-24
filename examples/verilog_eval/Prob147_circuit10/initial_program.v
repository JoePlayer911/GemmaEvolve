module TopModule (
  input clk,
  input a,
  input b,
  output q,
  output state
);

  // Default assignments (required for synthesis)
  assign q = 0;
  assign state = 0;

endmodule