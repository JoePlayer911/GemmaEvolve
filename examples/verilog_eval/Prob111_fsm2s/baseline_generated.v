module TopModule (
  input clk,
  input j,
  input k,
  input reset,
  output out
);

  // Define the states
  parameter OFF = 2'b00;
  parameter ON = 2'b01;

  // State register
  reg state;

  // Output logic
  assign out = (state == ON) ? 1 : 0;

  // State transition logic
  always @(posedge clk) begin
    if (reset) begin
      state <= OFF;
    end else begin
      case (state)
        OFF: begin
          if (j) begin
            state <= ON;
          end else begin
            state <= OFF;
          end
        end
        ON: begin
          if (k) begin
            state <= OFF;
          end else begin
            state <= ON;
          end
        end
        default: state <= OFF; // Should never happen, but good practice
      endcase
    end
  end

endmodule