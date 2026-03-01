module TopModule (
  input clk,
  input areset,
  input bump_left,
  input bump_right,
  input ground,
  input dig,
  output walk_left,
  output walk_right,
  output aaah,
  output digging
);

  reg walk_direction; // 0 = left, 1 = right
  reg falling;
  reg fall_count;
  reg digging_state;

  always @(posedge clk) begin
    if (areset) begin
      walk_direction <= 1; // Start walking right
      falling <= 0;
      fall_count <= 0;
      digging_state <= 0;
    end else begin
      if (falling) begin
        fall_count <= fall_count + 1;
        walk_direction <= walk_direction; // Maintain direction
        digging_state <= 0;
      end else begin
        fall_count <= 0;

        if (bump_left) begin
          walk_direction <= 1;
        end else if (bump_right) begin
          walk_direction <= 0;
        end else begin
          walk_direction <= walk_direction; // Maintain direction
        end

        if (ground) begin
          falling <= 0;
          if (dig) begin
            digging_state <= 1;
          end else begin
            digging_state <= 0;
          end
        end else begin
          falling <= 1;
          digging_state <= 0;
        end
      end
    end
  end

  assign walk_left = (walk_direction == 0);
  assign walk_right = (walk_direction == 1);
  assign aaah = (falling && (fall_count > 20) && ground);
  assign digging = (digging_state == 1);

endmodule