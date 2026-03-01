module TopModule (
  input a,
  input b,
  input c,
  input d,
  input e,
  output [24:0] out
);

  assign out[0] = (a == b);
  assign out[1] = (a == c);
  assign out[2] = (a == d);
  assign out[3] = (a == e);
  assign out[4] = (b == c);
  assign out[5] = (b == d);
  assign out[6] = (b == e);
  assign out[7] = (c == d);
  assign out[8] = (c == e);
  assign out[9] = (d == e);
  assign out[10] = (a == a);
  assign out[11] = (b == b);
  assign out[12] = (c == c);
  assign out[13] = (d == d);
  assign out[14] = (e == e);
  assign out[15] = (a == b);
  assign out[16] = (a == c);
  assign out[17] = (a == d);
  assign out[18] = (a == e);
  assign out[19] = (b == c);
  assign out[20] = (b == d);
  assign out[21] = (b == e);
  assign out[22] = (c == d);
  assign out[23] = (c == e);
  assign out[24] = (d == e);

endmodule