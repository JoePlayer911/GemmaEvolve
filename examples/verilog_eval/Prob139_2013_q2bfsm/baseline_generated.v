module TopModule (
  input clk,
  input resetn,
  input x,
  input y,
  output f,
  output g
);

  reg state;
  reg x_prev1;
  reg x_prev2;
  reg g_internal;

  always @(posedge clk or negedge resetn) begin
    if (!resetn) begin
      state <= 'A';
      x_prev1 <= 0;
      x_prev2 <= 0;
      g_internal <= 0;
      f <= 0;
      g <= 0;
    end else begin
      case (state)
        'A: begin
          f <= 1;
          state <= 'B';
        end
        'B: begin
          state <= 'C';
        end
        'C: begin
          if (x) begin
            x_prev1 <= 1;
            x_prev2 <= x_prev1;
          end else begin
            x_prev1 <= 0;
            x_prev2 <= x_prev1;
          end

          if (x_prev1 == 1 && x_prev2 == 0 && x) begin
            g_internal <= 1;
            state <= 'D';
          end else begin
            state <= 'C';
          end
        end
        'D: begin
          g <= g_internal;
          if (y) begin
            state <= 'C';
          end else begin
            state <= 'E';
          end
        end
        'E: begin
          if (!y) begin
            g_internal <= 0;
            g <= g_internal;
            state <= 'C';
          end else begin
            state <= 'D';
          end
        end
        default: begin
          state <= 'A';
        end
      endcase
    end
  end

endmodule