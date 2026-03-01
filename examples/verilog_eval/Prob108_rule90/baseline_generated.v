module TopModule (
  input clk,
  input load,
  input [511:0] data,
  output reg [511:0] q
);

  reg [511:0] next_q;

  integer i;

  always @(posedge clk) begin
    if (load) begin
      q <= data;
    end else begin
      q <= next_q;
    end
  end

  always @(*) begin
    for (i = 0; i < 512; i = i + 1) begin
      if (i == 0) begin
        next_q[i] = q[i] ^ 1'b0; // Left boundary always off
      end else if (i == 511) begin
        next_q[i] = q[i] ^ 1'b0; // Right boundary always off
      end else begin
        next_q[i] = q[i] ^ q[i-1] ^ q[i+1];
      end
    end
  end

endmodule