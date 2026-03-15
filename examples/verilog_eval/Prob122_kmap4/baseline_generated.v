module TopModule (
    input a,
    input b,
    input c,
    input d,
    output reg out
);
    wire eq_a_d;
    wire eq_b_c;

    assign eq_a_d = (a == d);
    assign eq_b_c = (b == c);

    always @(*) begin
        out = eq_a_d && eq_b_c;
    end
endmodule