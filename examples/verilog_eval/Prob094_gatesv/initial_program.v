module TopModule (
  input [3:0] in,
  output [2:0] out_both,
  output [3:1] out_any,
  output [3:0] out_different
);

  // Default output assignments (important for synthesis)
  assign out_both = 0;
  assign out_any = 0;
  assign out_different = 0;

endmodule