module TopModule (
  input clk,
  input areset,
  input predict_valid,
  input predict_taken,
  output logic [31:0] predict_history,

  input train_mispredicted,
  input train_taken,
  input [31:0] train_history
);

  logic [31:0] next_predict_history;

  always_ff @(posedge clk or posedge areset) begin
    if (areset) begin
      predict_history <= 32'b0;
    end else if (train_mispredicted) begin
      predict_history <= {train_history, train_taken};
    end else if (predict_valid) begin
      predict_history <= {predict_taken, predict_history[31:1]};
    end else begin
      predict_history <= predict_history;
    end
  end

endmodule