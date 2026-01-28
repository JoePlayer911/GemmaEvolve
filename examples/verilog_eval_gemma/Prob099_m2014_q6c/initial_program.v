module TopModule (
  input [6:1] y,
  input w,
  output Y2,
  output Y4
);

  // Default output assignments (important for synthesis)
  assign Y2 = 0;
  assign Y4 = 0;

endmodule