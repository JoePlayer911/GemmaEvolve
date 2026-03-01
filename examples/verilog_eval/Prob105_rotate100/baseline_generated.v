module TopModule (
  input clk,
  input load,
  input [1:0] ena,
  input [99:0] data,
  output reg [99:0] q
);

  reg [99:0] temp_q;

  always @(posedge clk) begin
    if (load) begin
      temp_q <= data;
    end else begin
      case (ena)
        2'b00: temp_q <= q; // No change
        2'b01: temp_q <= {q[98:0], q[0]}; // Rotate right by one
        2'b10: temp_q <= {q[1:99], q[0]}; // Rotate left by one
        default: temp_q <= q; // No change (default case for safety)
      endcase
    end
  end

  q <= temp_q;

endmodule