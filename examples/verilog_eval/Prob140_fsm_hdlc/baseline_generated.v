module TopModule (
  input clk,
  input reset,
  input in,
  output disc,
  output flag,
  output err
);

  reg [2:0] state;
  reg disc_r, flag_r, err_r;

  always @(posedge clk) begin
    if (reset) begin
      state <= 3'b000;
      disc_r <= 0;
      flag_r <= 0;
      err_r <= 0;
    end else begin
      case (state)
        3'b000: begin // Initial state, 0 consecutive 1s
          if (in)
            state <= 3'b001;
          else
            state <= 3'b000;
        end
        3'b001: begin // 1 consecutive 1
          if (in)
            state <= 3'b010;
          else
            state <= 3'b000;
        end
        3'b010: begin // 2 consecutive 1s
          if (in)
            state <= 3'b011;
          else
            state <= 3'b000;
        end
        3'b011: begin // 3 consecutive 1s
          if (in)
            state <= 3'b100;
          else
            state <= 3'b000;
        end
        3'b100: begin // 4 consecutive 1s
          if (in)
            state <= 3'b101;
          else
            state <= 3'b000;
        end
        3'b101: begin // 5 consecutive 1s
          if (in)
            state <= 3'b110;
          else
            state <= 3'b000;
        end
        3'b110: begin // 6 consecutive 1s
          if (in)
            state <= 3'b111;
          else
            state <= 3'b000;
        end
        3'b111: begin // 7 consecutive 1s
          if (in)
            state <= 3'b111; // Error condition, stays in error state
          else
            state <= 3'b000;
        end
      endcase
    end
  end

  assign disc = disc_r;
  assign flag = flag_r;
  assign err = err_r;

  always @(posedge clk) begin
    if (reset) begin
      disc_r <= 0;
      flag_r <= 0;
      err_r <= 0;
    end else begin
      if (state == 3'b110) begin
        disc_r <= 1;
      end else if (state == 3'b111) begin
        flag_r <= 1;
        err_r <= 1;
      end else begin
        disc_r <= 0;
        flag_r <= 0;
        err_r <= 0;
      end
    end
  end

endmodule