module TopModule (
  input clk,
  input in,
  input areset,
  output out
);

  // Define the states
  parameter A = 2'b00
  parameter B = 2'b01
  parameter C = 2'b10
  parameter D = 2'b11

  // State register
  reg [1:0] current_state;

  // Output logic
  assign out = current_state;

  // State transition logic
  always @(posedge clk or posedge areset) begin
    if (areset) begin
      current_state <= A;
    end else begin
      case (current_state)
        A: begin
          if (in) begin
            current_state <= B;
          end else begin
            current_state <= A;
          end
        end
        B: begin
          if (in) begin
            current_state <= C;
          end else begin
            current_state <= A;
          end
        end
        C: begin
          if (in) begin
            current_state <= D;
          end else begin
            current_state <= C;
          end
        end
        D: begin
          if (in) begin
            current_state <= A;
          end else begin
            current_state <= C;
          end
        end
        default: begin
          current_state <= A; // Should not happen, but good practice
        end
      endcase
    end
  end

endmodule