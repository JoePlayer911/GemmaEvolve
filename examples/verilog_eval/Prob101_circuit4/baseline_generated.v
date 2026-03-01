module TopModule (
  input a,
  input b,
  input c,
  input d,
  output q
);

  assign q = (a == 0 && d == 0) ? 0 : 1;

endmodule