module TopModule (
  input clk,
  input reset,
  input w,
  output z
);

  // Define state encoding
  localparam STATE_A = 6'b000000;
  localparam STATE_B = 6'b000001;
  localparam STATE_C = 6'b000010;
  localparam STATE_D = 6'b000011;
  localparam STATE_E = 6'b000100;
  localparam STATE_F = 6'b000101;

  // State register
  reg [5:0] current_state;

  // State table (always block)
  always @(posedge clk or posedge reset) begin
    if (reset) begin
      current_state <= STATE_A;
    end else begin
      case (current_state)
        STATE_A: begin
          if (w) begin
            current_state <= STATE_B;
          end else begin
            current_state <= STATE_A;
          end
        end
        STATE_B: begin
          if (w) begin
            current_state <= STATE_C;
          end else begin
            current_state <= STATE_A;
          end
        end
        STATE_C: begin
          if (w) begin
            current_state <= STATE_D;
          end else begin
            current_state <= STATE_E;
          end
        end
        STATE_D: begin
          if (w) begin
            current_state <= STATE_E;
          end else begin
            current_state <= STATE_F;
          end
        end
        STATE_E: begin
          if (w) begin
            current_state <= STATE_F;
          end else begin
            current_state <= STATE_A;
          end
        end
        STATE_F: begin
          if (w) begin
            current_state <= STATE_A;
          end else begin
            current_state <= STATE_E;
          end
        end
        default: begin
          current_state <= STATE_A; // Default to state A in case of an undefined state
        end
      endcase
    end
  end

  // Output logic (assign statement)
  assign z = (current_state == STATE_B) | (current_state == STATE_D) | (current_state == STATE_F);

endmodule