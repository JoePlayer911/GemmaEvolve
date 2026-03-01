module TopModule (
  input clk,
  input reset,
  output [3:1] ena,
  output reg [15:0] q
);

  reg [3:0] digit_0;
  reg [3:0] digit_1;
  reg [3:0] digit_2;
  reg [3:0] digit_3;

  assign q = {digit_3, digit_2, digit_1, digit_0};

  assign ena[0] = ~digit_0[0];
  assign ena[1] = ~digit_1[0];
  assign ena[2] = ~digit_2[0];
  assign ena[3] = ~digit_3[0];

  always @(posedge clk) begin
    if (reset) begin
      digit_0 <= 4'b0000;
      digit_1 <= 4'b0000;
      digit_2 <= 4'b0000;
      digit_3 <= 4'b0000;
    end else begin
      if (ena[0]) begin
        if (digit_0 == 4'b1001) begin
          digit_0 <= 4'b0000;
        end else begin
          digit_0 <= digit_0 + 1;
        end
      end
      if (ena[1]) begin
        if (digit_1 == 4'b1001) begin
          digit_1 <= 4'b0000;
        end else begin
          digit_1 <= digit_1 + 1;
        end
      end
      if (ena[2]) begin
        if (digit_2 == 4'b1001) begin
          digit_2 <= 4'b0000;
        end else begin
          digit_2 <= digit_2 + 1;
        end
      end
      if (ena[3]) begin
        if (digit_3 == 4'b1001) begin
          digit_3 <= 4'b0000;
        end else begin
          digit_3 <= digit_3 + 1;
        end
      end
    end
  end

endmodule