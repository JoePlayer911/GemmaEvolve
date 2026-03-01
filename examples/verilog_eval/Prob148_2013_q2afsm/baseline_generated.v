module TopModule (
  input clk,
  input resetn,
  input [3:1] r,
  output [3:1] g
);

  reg [3:1] current_state;

  // State definition
  localparam A = 4'b0000;
  localparam GRANT_1 = 4'b0001;
  localparam GRANT_2 = 4'b0010;
  localparam GRANT_3 = 4'b0011;

  always @(posedge clk or negedge resetn) begin
    if (!resetn) begin
      current_state <= A;
      g <= 4'b0000;
    end else begin
      case (current_state)
        A: begin
          g <= 4'b0000;
          if (r[1]) begin
            current_state <= GRANT_1;
          end else if (r[2]) begin
            current_state <= GRANT_2;
          end else if (r[3]) begin
            current_state <= GRANT_3;
          end
        end
        GRANT_1: begin
          g[1] <= 1'b1;
          g[2] <= 1'b0;
          g[3] <= 1'b0;
          if (!r[1]) begin
            current_state <= A;
          end
        end
        GRANT_2: begin
          g[1] <= 1'b0;
          g[2] <= 1'b1;
          g[3] <= 1'b0;
          if (!r[2]) begin
            current_state <= A;
          end
        end
        GRANT_3: begin
          g[1] <= 1'b0;
          g[2] <= 1'b0;
          g[3] <= 1'b1;
          if (!r[3]) begin
            current_state <= A;
          end
        end
        default: begin
          current_state <= A;
          g <= 4'b0000;
        end
      endcase
    end
  end

endmodule