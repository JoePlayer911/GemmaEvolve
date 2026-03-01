module TopModule (
  input clk,
  input reset,
  output reg [9:0] q
);

  reg [9:0] count;

  always @(posedge clk) begin
    if (reset) begin
      count <= 0;
    end else begin
      if (count == 999) begin
        count <= 0;
      end else begin
        count <= count + 1;
      end
    end
  end

  assign q = count;

endmodule