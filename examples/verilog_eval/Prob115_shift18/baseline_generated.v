module TopModule (
  input clk,
  input load,
  input ena,
  input [1:0] amount,
  input [63:0] data,
  output reg [63:0] q
);

  reg [63:0] temp_q;

  always @(posedge clk) begin
    if (load) begin
      q <= data;
    end else if (ena) begin
      case (amount)
        2'b00: q <= q; // No shift
        2'b01: q <= {q[62:0], 1'b0}; // Left shift by 1
        2'b10: q <= {1'b0, q[63:1]}; // Right shift by 1 (arithmetic)
        2'b11: begin // Left shift by 8 or Right shift by 8
          if (q[63]) begin // Arithmetic Right Shift
            q <= {8'hFFFFFFFF, q[63:8]};
          end else begin // Logical Right Shift
            q <= {8'b0, q[63:8]};
          end
        end
      endcase
    end else begin
      q <= q; // Hold
    end
  end

endmodule