module TopModule (
  input clk,
  input areset,
  input bump_left,
  input bump_right,
  input ground,
  output walk_left,
  output walk_right,
  output aaah
);

  reg state;
  reg dir;

  always @(posedge clk or posedge areset) begin
    if (areset) begin
      state <= 2; // Walking left
      dir <= 1;
    end else begin
      case (state)
        2: begin // Walking left
          walk_left <= 1;
          walk_right <= 0;
          aaah <= 0;
          if (bump_right) begin
            state <= 3; // Walking right
            dir <= 0;
          end else if (!ground) begin
            state <= 1; // Falling
            aaah <= 1;
          end
        end
        3: begin // Walking right
          walk_left <= 0;
          walk_right <= 1;
          aaah <= 0;
          if (bump_left) begin
            state <= 2; // Walking left
            dir <= 1;
          end else if (!ground) begin
            state <= 1; // Falling
            aaah <= 1;
          end
        end
        1: begin // Falling
          walk_left <= 0;
          walk_right <= 0;
          aaah <= 1;
          if (ground) begin
            state <= dir; // Resume walking in previous direction
          end
        end
        default: begin
          state <= 2;
          dir <= 1;
        end
      endcase
    end
  end

endmodule