module TopModule (
  input clk,
  input reset,
  input data,
  output reg shift_ena,
  output reg counting,
  input done_counting,
  output reg done,
  input ack
);

  reg [3:0] state;
  reg [3:0] data_reg;
  reg detect;

  localparam IDLE = 4'b0000;
  localparam S1 = 4'b0001;
  localparam S2 = 4'b0010;
  localparam S3 = 4'b0011;
  localparam S4 = 4'b0100;
  localparam COUNTING = 4'b0101;
  localparam DONE = 4'b0110;
  localparam WAIT_ACK = 4'b0111;

  always @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      shift_ena <= 0;
      counting <= 0;
      done <= 0;
      data_reg <= 0;
      detect <= 0;
    end else begin
      case (state)
        IDLE: begin
          shift_ena <= 0;
          counting <= 0;
          done <= 0;
          if (data == 1) begin
            data_reg <= 1;
            state <= S1;
          end else begin
            data_reg <= 0;
            state <= IDLE;
          end
        end
        S1: begin
          shift_ena <= 0;
          counting <= 0;
          done <= 0;
          if (data == 1) begin
            data_reg <= 2;
            state <= S2;
          end else begin
            data_reg <= 0;
            state <= IDLE;
          end
        end
        S2: begin
          shift_ena <= 0;
          counting <= 0;
          done <= 0;
          if (data == 0) begin
            data_reg <= 2;
            state <= S3;
          end else begin
            data_reg <= 0;
            state <= IDLE;
          end
        end
        S3: begin
          shift_ena <= 0;
          counting <= 0;
          done <= 0;
          if (data == 1) begin
            data_reg <= 2;
            state <= S4;
          end else begin
            data_reg <= 0;
            state <= IDLE;
          end
        end
        S4: begin
          shift_ena <= 1;
          counting <= 0;
          done <= 0;
          data_reg <= {data_reg[2:0], data};
          state <= COUNTING;
        end
        COUNTING: begin
          shift_ena <= 0;
          counting <= 1;
          done <= 0;
          if (done_counting) begin
            state <= DONE;
          end
        end
        DONE: begin
          shift_ena <= 0;
          counting <= 0;
          done <= 1;
          if (ack) begin
            state <= IDLE;
          end
        end
        WAIT_ACK: begin
          shift_ena <= 0;
          counting <= 0;
          done <= 1;
          if (ack) begin
            state <= IDLE;
          end
        end
        default: begin
          state <= IDLE;
        end
      endcase
    end
  end

endmodule