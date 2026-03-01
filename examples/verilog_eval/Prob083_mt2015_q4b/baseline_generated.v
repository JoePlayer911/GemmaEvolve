module TopModule (
  input x,
  input y,
  output z
);

  assign z = (x == 0 && y == 0) || (x == 1 && y == 1);

endmodule