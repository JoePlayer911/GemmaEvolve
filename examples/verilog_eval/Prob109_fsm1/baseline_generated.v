module TopModule (
  input clk,
  input in,
  input areset,
  output out
);

  reg state;

  always @(posedge clk or posedge areset) begin
    if (areset) begin
      state <= 1'b1; // State B
    end else begin
      case (state)
        1'b0: begin // State A
          if (in == 1'b1) begin
            state <= 1'b0;
          end else begin
            state <= 1'b1;
          end
        end
        1'b1: begin // State B
          if (in == 1'b0) begin
            state <= 1'b0;
          end else begin
            state <= 1'b1;
          end
        end
        default: state <= 1'b0;
      endcase
    end
  end

  assign out = state; // Output depends on the current state

endmodule