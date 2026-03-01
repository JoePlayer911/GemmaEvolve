module TopModule (
  input [99:0] in,
  output reg [99:0] out
);

  genvar i;
  generate
    for (i = 0; i < 100; i++) begin : bit_reverse
      assign out[i] = in[99-i];
    end
  endgenerate

endmodule