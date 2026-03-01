module TopModule (
  input [7:0] a,
  input [7:0] b,
  input [7:0] c,
  input [7:0] d,
  output reg [7:0] min
);

  reg [7:0] min_ab;
  reg [7:0] min_abcd;

  assign min_ab = (a < b) ? a : b;

  reg [7:0] min_cd;
  assign min_cd = (c < d) ? c : d;

  assign min_abcd = (min_ab < min_cd) ? min_ab : min_cd;

  min = min_abcd;

endmodule