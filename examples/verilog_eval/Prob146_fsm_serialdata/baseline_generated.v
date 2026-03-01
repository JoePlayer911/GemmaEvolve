module TopModule (
  input clk,
  input in,
  input reset,
  output [7:0] out_byte,
  output done
);

  // Internal signals
  reg [7:0] rx_data;
  reg [2:0] state;
  reg done_reg;

  // Assign the done output
  assign done = done_reg;

  // Assign the output byte
  assign out_byte = rx_data;

  // State definitions
  localparam IDLE = 3'b000;
  localparam START_BIT = 3'b001;
  localparam DATA_BITS = 3'b010;
  localparam STOP_BIT = 3'b011;
  localparam ERROR = 3'b100;

  always @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      rx_data <= 8'b0;
      done_reg <= 0;
    end else begin
      case (state)
        IDLE: begin
          if (in == 0) begin
            state <= START_BIT;
          end
        end
        START_BIT: begin
          if (in == 0) begin
            state <= DATA_BITS;
            rx_data <= 8'b0;
          end else begin
            state <= IDLE;
          end
        end
        DATA_BITS: begin
          if (in == 0) begin
            rx_data <= {rx_data[6:0], 1'b0};
          end else begin
            rx_data <= {rx_data[6:0], 1'b1};
          end
          if ($count == 8) begin
            state <= STOP_BIT;
            $count <= 0;
          end
          else begin
            $count <= $count + 1;
          end
        end
        STOP_BIT: begin
          if (in == 1) begin
            state <= IDLE;
            done_reg <= 1;
            $count <= 0;
          end else begin
            state <= ERROR;
            $count <= 0;
          end
        end
        ERROR: begin
          if (in == 1) begin
            state <= IDLE;
            done_reg <= 0;
            $count <= 0;
          end else begin
            state <= ERROR;
          end
        end
        default: begin
          state <= IDLE;
          done_reg <= 0;
          $count <= 0;
        end
      endcase
    end
  end

  reg [$count = 0];

endmodule