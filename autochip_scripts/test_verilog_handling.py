from verilog_handling import compile_and_simulate_verilog
import languagemodels as lm

# Paths to your design and testbench files
design_file = r"C:\Users\tirmi\autochip_activehdl_2\AutoChip\autochip_scripts\counter.v"
testbench_file = r"C:\Users\tirmi\autochip_activehdl_2\AutoChip\autochip_scripts\counter_tb.v"

# Sample Verilog code for testing
full_text = """
module counter (
    input wire clk,
    input wire rst,
    output reg [3:0] count
);
    always @(posedge clk or posedge rst) begin
        if (rst)
            count <= 4'b0000;
        else
            count <= count + 1;
    end
endmodule
"""

# Create an LLMResponse instance with the sample Verilog code
response = lm.LLMResponse(iteration=1, response_num=1, full_text=full_text)
response.set_parsed_text(full_text)  # Set parsed_text explicitly

# Run the compile and simulate function
return_code, stderr, stdout = compile_and_simulate_verilog(design_file, testbench_file, response)

# Print the output to verify
print("Return Code:", return_code)
print("Standard Output:", stdout)
print("Standard Error:", stderr)
