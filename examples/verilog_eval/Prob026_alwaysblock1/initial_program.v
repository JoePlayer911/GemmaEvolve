module TopModule (
  input a,
  input b,
  output out_assign,
  output reg out_alwaysblock
);

  // Default assignment to satisfy synthesis requirements.  Crucial for avoiding errors.
  assign out_assign = 0; 

endmodule