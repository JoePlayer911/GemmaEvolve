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

  // Define states
  localparam STATE_WALK_LEFT = 2'b00;
  localparam STATE_WALK_RIGHT = 2'b01;
  localparam STATE_AAAH = 2'b10;
  localparam STATE_DIG = 2'b11;

  reg [1:0] current_state;
  reg [1:0] next_state;

  // State register update
  always @(posedge clk or posedge areset) begin
    if (areset) begin
      current_state <= STATE_WALK_LEFT;
    end else begin
      current_state <= next_state;
    end
  end

  // Next state logic
  always @(*) begin
    next_state = current_state; // Default: stay in the same state

    case (current_state)
      STATE_WALK_LEFT: begin
        if (bump_right) begin
          next_state = STATE_WALK_RIGHT;
        end else if (!ground) begin
          next_state = STATE_AAAH;
        end else if (dig) begin
          next_state = STATE_DIG;
        end
      end
      STATE_WALK_RIGHT: begin
        if (bump_left) begin
          next_state = STATE_WALK_LEFT;
        end else if (!ground) begin
          next_state = STATE_AAAH;
        end else if (dig) begin
          next_state = STATE_DIG;
        end
      end
      STATE_AAAH: begin
        if (ground) begin
          next_state = STATE_WALK_LEFT; // Resume walking left
        end
      end
      STATE_DIG: begin
        if (!ground) begin
          next_state = STATE_AAAH;
        end
      end
    endcase
  end

  // Output logic
  assign walk_left = (current_state == STATE_WALK_LEFT);
  assign walk_right = (current_state == STATE_WALK_RIGHT);
  assign aaah = (current_state == STATE_AAAH);
  assign digging = (current_state == STATE_DIG);

endmodule