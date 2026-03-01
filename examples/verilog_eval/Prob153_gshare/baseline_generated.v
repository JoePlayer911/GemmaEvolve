module TopModule (
  input clk,
  input areset,

  input predict_valid,
  input [6:0] predict_pc,
  output predict_taken,
  output [6:0] predict_history,

  input train_valid,
  input train_taken,
  input train_mispredicted,
  input [6:0] train_history,
  input [6:0] train_pc
);

  // Internal signals
  reg [6:0] global_history;
  reg [7:0] pht [0:127];
  reg [6:0] index;

  // Predictor logic
  always @(posedge clk or posedge areset) begin
    if (areset) begin
      global_history <= 0;
      for (integer i = 0; i < 128; i = i + 1) begin
        pht[i] <= 0;
      end
    end else begin
      if (predict_valid) begin
        index <= predict_pc[6:0] ^ global_history;
        predict_taken <= (pht[index] >= 2);
        predict_history <= global_history;
      end
    end
  end

  // Training logic
  always @(posedge clk or posedge areset) begin
    if (areset) begin
      global_history <= 0;
    end else if (train_valid) begin
      index <= train_pc[6:0] ^ train_history;
      if (train_taken) begin
        if (pht[index] < 3) begin
          pht[index] <= pht[index] + 1;
        end
      end else begin
        if (pht[index] > 0) begin
          pht[index] <= pht[index] - 1;
        end
      end

      // Misprediction recovery
      if (train_mispredicted) begin
        // Recover global history.  This is tricky since we don't have the history
        // *before* the misprediction. We must assume the history was valid *before*
        // the misprediction, and therefore must update it.
        global_history <= train_history;
      end else begin
        global_history <= train_history;
      end
    end
  end

endmodule