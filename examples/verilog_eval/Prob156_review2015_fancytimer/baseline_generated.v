module TopModule (
  input wire clk,
  input wire reset,
  input wire data,
  output wire [3:0] count,
  output reg counting,
  output reg done,
  input wire ack
);

  reg [3:0] delay;
  reg [3:0] state;
  reg [3:0] count_reg;
  reg [3:0] target_count;
  reg start_sequence;
  reg [3:0] sequence_buffer;
  reg sequence_valid;

  // State machine states
  localparam IDLE = 0;
  localparam SEQUENCE_DETECT = 1;
  localparam DELAY_CAPTURE = 2;
  localparam COUNTING = 3;
  localparam DONE = 4;

  // Sequence detection
  always @(posedge clk) begin
    if (reset) begin
      start_sequence <= 0;
      sequence_buffer <= 0;
      sequence_valid <= 0;
    end else begin
      if (sequence_valid) begin
        sequence_valid <= 0;
      end else begin
        sequence_buffer <= {sequence_buffer[2:0], data};
        if (sequence_buffer == 4'b1101) begin
          start_sequence <= 1;
          sequence_valid <= 1;
        end else begin
          start_sequence <= 0;
        end
      end
    end
  end

  // State machine logic
  always @(posedge clk) begin
    if (reset) begin
      state <= IDLE;
      counting <= 0;
      done <= 0;
      count <= 0;
    end else begin
      case (state)
        IDLE: begin
          if (start_sequence) begin
            state <= SEQUENCE_DETECT;
            counting <= 0;
            done <= 0;
          end else begin
            state <= IDLE;
          end
        end
        SEQUENCE_DETECT: begin
          state <= DELAY_CAPTURE;
          counting <= 0;
          done <= 0;
        end
        DELAY_CAPTURE: begin
          delay <= data;
          state <= COUNTING;
          target_count <= delay + 1;
          count_reg <= target_count;
          counting <= 1;
          done <= 0;
        end
        COUNTING: begin
          if (count_reg == 0) begin
            state <= DONE;
            counting <= 0;
            done <= 1;
          end else begin
            count_reg <= count_reg - 1;
          end
        end
        DONE: begin
          if (ack) begin
            state <= IDLE;
            counting <= 0;
            done <= 0;
          end else begin
            state <= DONE;
            counting <= 0;
            done <= 1;
          end
        end
        default: begin
          state <= IDLE;
          counting <= 0;
          done <= 0;
        end
      endcase
    end
  end

  assign count = count_reg;

endmodule