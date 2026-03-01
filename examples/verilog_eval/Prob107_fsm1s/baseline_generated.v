module TopModule (
  input clk,
  input in,
  input reset,
  output out
);

  reg state;

  always @(posedge clk) begin
    if (reset) begin
      state <= 1; // State B
    end else begin
      case (state)
        1: begin // State B
          if (in) begin
            state <= 1; // Remain in state B
          end else begin
            state <= 0; // Transition to state A
          end
        end
        0: begin // State A
          if (in) begin
            state <= 0; // Remain in state A
          end else begin
            state <= 1; // Transition to state B
          end
        end
        default: state <= 0; // Should not happen, but handle for safety
      endcase
    end
  end

  assign out = state;

endmodule