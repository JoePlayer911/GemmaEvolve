module TopModule (
  input clk,
  input shift_ena,
  input count_ena,
  input data,
  output reg [3:0] q
);

  reg [3:0] temp_q;

  always @(posedge clk) begin
    if (shift_ena) begin
      temp_q[3] <= data;
      for (integer i = 3; i > 0; i = i - 1) begin
        temp_q[i] <= temp_q[i-1];
      end
    end else if (count_ena) begin
      temp_q <= temp_q - 1'b1;
    end
  end

  assign q = temp_q;

endmodule