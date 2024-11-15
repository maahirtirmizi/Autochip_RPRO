`timescale 1ns / 1ps
`define RESET_VAL 4'b0000

module reference_module(
    input [2:0] vec, 
    output [2:0] outv,
    output o2,
    output o1,
    output o0
);
    assign outv = vec;
    assign {o2, o1, o0} = vec;
endmodule

module stimulus_gen (
    input clk,
    output reg [2:0] vec,
    output reg [511:0] wavedrom_title,
    output reg wavedrom_enable
);
    task wavedrom_start(input [511:0] title = "");
    begin
        wavedrom_title <= title;
        wavedrom_enable <= 1;
    end
    endtask

    task wavedrom_stop;
    begin
        wavedrom_enable <= 0;
    end
    endtask

    initial begin
        int count = 0;
        vec <= 3'b000;
        @(negedge clk);
        wavedrom_start("Vector0 Simulation");
        repeat (10) @(posedge clk)
            vec <= count++;
        wavedrom_stop();
        #1 $finish;
    end
endmodule

module vector0_tb();

    typedef struct packed {
        int errors;
        int errortime;
        int errors_outv;
        int errortime_outv;
        int errors_o2;
        int errortime_o2;
        int errors_o1;
        int errortime_o1;
        int errors_o0;
        int errortime_o0;
        int clocks;
    } stats;

    stats stats1;

    wire [511:0] wavedrom_title;
    wire wavedrom_enable;
    reg clk = 0;

    logic [2:0] vec;
    logic [2:0] outv_ref;
    logic [2:0] outv_dut;
    logic o2_ref;
    logic o2_dut;
    logic o1_ref;
    logic o1_dut;
    logic o0_ref;
    logic o0_dut;

    initial forever #5 clk = ~clk;

    initial begin 
        $dumpfile("wave.vcd");
        $dumpvars(1, stim1.clk, tb_mismatch, vec, outv_ref, outv_dut, o2_ref, o2_dut, o1_ref, o1_dut, o0_ref, o0_dut);
    end

    wire tb_match;        // Verification
    wire tb_mismatch = ~tb_match;

    stimulus_gen stim1 (
        .clk(clk),
        .vec(vec),
        .wavedrom_title(wavedrom_title),
        .wavedrom_enable(wavedrom_enable)
    );

    reference_module good1 (
        .vec(vec),
        .outv(outv_ref),
        .o2(o2_ref),
        .o1(o1_ref),
        .o0(o0_ref)
    );

    top_module top_module1 (
        .vec(vec),
        .outv(outv_dut),
        .o2(o2_dut),
        .o1(o1_dut),
        .o0(o0_dut)
    );

    bit strobe = 0;

    task wait_for_end_of_timestep;
    begin
        repeat (5) begin
            strobe <= !strobe;
            @(strobe);
        end
    end
    endtask    

    final begin
        if (stats1.errors_outv) $display("Hint: Output '%s' has %0d mismatches. First mismatch occurred at time %0d.", "outv", stats1.errors_outv, stats1.errortime_outv);
        else $display("Hint: Output '%s' has no mismatches.", "outv");
        if (stats1.errors_o2) $display("Hint: Output '%s' has %0d mismatches. First mismatch occurred at time %0d.", "o2", stats1.errors_o2, stats1.errortime_o2);
        else $display("Hint: Output '%s' has no mismatches.", "o2");
        if (stats1.errors_o1) $display("Hint: Output '%s' has %0d mismatches. First mismatch occurred at time %0d.", "o1", stats1.errors_o1, stats1.errortime_o1);
        else $display("Hint: Output '%s' has no mismatches.", "o1");
        if (stats1.errors_o0) $display("Hint: Output '%s' has %0d mismatches. First mismatch occurred at time %0d.", "o0", stats1.errors_o0, stats1.errortime_o0);
        else $display("Hint: Output '%s' has no mismatches.", "o0");

        $display("Hint: Total mismatched samples is %1d out of %1d samples\n", stats1.errors, stats1.clocks);
        $display("Simulation finished at %0d ps", $time);
        $display("Mismatches: %1d in %1d samples", stats1.errors, stats1.clocks);
    end

    assign tb_match = ( { outv_ref, o2_ref, o1_ref, o0_ref } === 
                       ( { outv_ref, o2_ref, o1_ref, o0_ref } ^ { outv_dut, o2_dut, o1_dut, o0_dut } ^ { outv_ref, o2_ref, o1_ref, o0_ref }));

    always @(posedge clk, negedge clk) begin
        stats1.clocks++;
        if (!tb_match) begin
            if (stats1.errors == 0) stats1.errortime = $time;
            stats1.errors++;
        end
        if (outv_ref !== (outv_ref ^ outv_dut ^ outv_ref)) begin
            if (stats1.errors_outv == 0) stats1.errortime_outv = $time;
            stats1.errors_outv++;
        end
        if (o2_ref !== (o2_ref ^ o2_dut ^ o2_ref)) begin
            if (stats1.errors_o2 == 0) stats1.errortime_o2 = $time;
            stats1.errors_o2++;
        end
        if (o1_ref !== (o1_ref ^ o1_dut ^ o1_ref)) begin
            if (stats1.errors_o1 == 0) stats1.errortime_o1 = $time;
            stats1.errors_o1++;
        end
        if (o0_ref !== (o0_ref ^ o0_dut ^ o0_ref)) begin
            if (stats1.errors_o0 == 0) stats1.errortime_o0 = $time;
            stats1.errors_o0++;
        end
    end
endmodule
