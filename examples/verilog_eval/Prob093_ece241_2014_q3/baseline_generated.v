module TopModule (
  input c,
  input d,
  output [3:0] mux_in
);

  wire s0, s1, s2, s3;

  assign mux_in[0] = c;
  assign mux_in[1] = d;
  assign mux_in[2] = c;
  assign mux_in[3] = d;

endmodule