module TopModule (
  input [4:0] a,
  input [4:0] b,
  input [4:0] c,
  input [4:0] d,
  input [4:0] e,
  input [4:0] f,
  output [7:0] w,
  output [7:0] x,
  output [7:0] y,
  output [7:0] z
);

  wire [31:0] concatenated_value;

  assign concatenated_value[31:24] = a;
  assign concatenated_value[23:16] = b;
  assign concatenated_value[15:8] = c;
  assign concatenated_value[7:0] = d;
  assign concatenated_value[19:12] = e;
  assign concatenated_value[11:4] = f;
  assign concatenated_value[31:30] = 2'b11;

  assign w = concatenated_value[31:24];
  assign x = concatenated_value[23:16];
  assign y = concatenated_value[15:8];
  assign z = concatenated_value[7:0];

endmodule