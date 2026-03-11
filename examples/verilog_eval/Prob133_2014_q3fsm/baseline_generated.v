module TopModule (
  input clk,
  input reset,
  input s,
  input w,
  output reg z
);

  reg [1:0] state;
  reg [1:0] w_history;
  reg two_ones_detected;

  // State transitions
  always @(posedge clk) begin
    if (reset) begin
      state <= 2'b00; // A
      z <= 0;
      two_ones_detected <= 0;
    end else begin
      case (state)
        2'b00: begin // A
          if (s) begin
            state <= 2'b01; // B
          end else begin
            state <= 2'b00; // A - stays in A if s is 0
          end
          z <= 0;
          two_ones_detected <= 0;
        end
        2'b01: begin // B
          w_history <= {w_history[1], w};
          
          if (w_history[0] == 1 && w_history[1] == 1) begin
            two_ones_detected <= 1;
          end else begin
            two_ones_detected <= 0;
          end

          if (two_ones_detected) begin
            z <= 1;
          end else begin
            z <= 0;
          end
        end
        default: begin
          state <= 2'b00;
          z <= 0;
          two_ones_detected <= 0;
        end
      endcase
    end
  end

endmodule