module TopModule (
  input do_sub,
  input [7:0] a,
  input [7:0] b,
  output reg [7:0] out,
  output reg result_is_zero
);

  reg [7:0] sum_sub;
  reg carry;

  assign carry = do_sub;

  assign sum_sub = a + (do_sub ? (~b + 1) : b);

  assign out = sum_sub;

  always @(*) begin
    if (out == 8'h00) begin
      result_is_zero = 1;
    end else begin
      result_is_zero = 0;
    end
  end

endmodule