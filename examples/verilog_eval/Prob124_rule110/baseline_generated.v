module TopModule (
  input clk,
  input load,
  input [511:0] data,
  output reg [511:0] q
);

  reg [511:0] next_q;

  always @(posedge clk) begin
    if (load) begin
      next_q <= data;
    end else begin
      next_q <= next_state;
    end
  end

  assign q <= next_q;

  reg [511:0] next_state;

  generate
    for (int i = 0; i < 512; i++) begin : gen_cell
      wire left_neighbor;
      wire right_neighbor;

      if (i == 0) begin
        left_neighbor = 0;
      end else begin
        left_neighbor = next_q[i-1];
      end

      if (i == 511) begin
        right_neighbor = 0;
      end else begin
        right_neighbor = next_q[i+1];
      end

      always_comb begin
        case ({left_neighbor, next_q[i], right_neighbor})
          3'b000: next_state[i] = 0;
          3'b001: next_state[i] = 1;
          3'b010: next_state[i] = 1;
          3'b011: next_state[i] = 1;
          3'b100: next_state[i] = 1;
          3'b101: next_state[i] = 1;
          3'b110: next_state[i] = 1;
          3'b111: next_state[i] = 0;
        endcase
      end
    end
  endgenerate

endmodule