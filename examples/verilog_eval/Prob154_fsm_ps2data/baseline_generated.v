module TopModule (
  input clk,
  input [7:0] in,
  input reset,
  output [23:0] out_bytes,
  output done
);

  // Internal signals
  reg [7:0] byte1, byte2, byte3;
  reg [2:0] state;
  reg done_reg;

  // State definition
  localparam IDLE = 3'b000;
  localparam SEARCH = 3'b001;
  localparam COLLECT1 = 3'b010;
  localparam COLLECT2 = 3'b011;
  localparam COLLECT3 = 3'b100;
  localparam OUTPUT = 3'b101;

  // State register update
  always @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      done_reg <= 0;
    end else begin
      case (state)
        IDLE: begin
          if (in[7]) begin
            state <= SEARCH;
          end else begin
            state <= IDLE;
          end
        end
        SEARCH: begin
          if (in[7]) begin
            byte1 <= in;
            state <= COLLECT1;
          end else begin
            state <= SEARCH;
          end
        end
        COLLECT1: begin
          byte2 <= in;
          state <= COLLECT2;
        end
        COLLECT2: begin
          byte3 <= in;
          state <= COLLECT3;
        end
        COLLECT3: begin
          state <= OUTPUT;
        end
        OUTPUT: begin
          state <= IDLE;
        end
      endcase
    end
  end

  // Output assignment
  assign out_bytes = {byte1, byte2, byte3};
  assign done = done_reg;

  always @(posedge clk) begin
    if (reset) begin
      done_reg <= 0;
    end else if (state == OUTPUT) begin
      done_reg <= 1;
    end else begin
      done_reg <= 0;
    end
  end

endmodule