module TopModule (
  input clk,
  input L,
  input q_in,
  input r_in,
  output reg Q
);

  reg [3:0] q;

  always @(posedge clk) begin
    if (L) begin
      q <= {q_in, r_in, 1'b0, r_in};
    end else begin
      q[0] <= q[0];
      q[1] <= q[1] ^ q[2];
      q[2] <= q[2];
      q[3] <= q[2];
    end
  end

  assign Q = q[0];

endmodule