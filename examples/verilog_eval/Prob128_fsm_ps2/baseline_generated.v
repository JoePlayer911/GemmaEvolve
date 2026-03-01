module TopModule (
  input clk,
  input [7:0] in,
  input reset,
  output done
);

  reg [1:0] state;
  reg done_reg;

  always @(posedge clk) begin
    if (reset) begin
      state <= 0;
      done_reg <= 0;
    end else begin
      case (state)
        0: begin // Initial state: Searching for the start byte
          if (in[3]) begin
            state <= 1;
          end else begin
            state <= 0;
          end
        end
        1: begin // State 1: Waiting for the second byte
          state <= 2;
        end
        2: begin // State 2: Waiting for the third byte
          state <= 3;
        end
        3: begin // State 3: Message complete
          done_reg <= 1;
          state <= 0;
        end
        default: begin
          state <= 0;
        end
      endcase
    end
  end

  assign done = done_reg;

endmodule