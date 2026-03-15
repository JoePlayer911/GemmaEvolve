module TopModule (
    input        clk,
    input  [7:0] d,
    input        reset,
    output reg [7:0] q
);
    // Synchronous reset of the 8‑bit register
    always @(posedge clk) begin
        if (reset)
            q <= 8'b0;
        else
            q <= d;
    end
endmodule