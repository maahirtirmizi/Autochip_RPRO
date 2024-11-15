import config_handler as c
import verilog_handling as vh
from rivierapro_backend import RivieraPROBackend  # Updated import
from conversation import Conversation
import os
from time import time
import re

def log_output(stage, details):
    print(f"\n{stage}:")
    print(details)
    print("=" * 50)

def extract_verilog_code(text):
    """Extract valid Verilog code from text, removing any conversational content."""
    lines = text.split('\n')
    valid_lines = []
    started = False
    for line in lines:
        if line.strip().startswith(('`define', 'module', '`timescale')):
            started = True
        if started and not line.strip().startswith(('Your', 'Here', 'I', 'The', 'This')):
            valid_lines.append(line)
    return '\n'.join(valid_lines)

def parse_compilation_errors(output):
    """Parse compilation errors to extract and format specific issues."""
    errors = []
    if "Missing semicolon" in output:
        errors.append("Error 1: Missing semicolon in the module or always block.")
    if "Unknown identifier" in output:
        errors.append("Error 2: Undefined identifier found, possibly `reset_signal` should be `rst`.")
    if "Syntax error" in output:
        errors.append("Error 3: Syntax error in the testbench; check the `$monitor` line.")
    if "Improper signal assignment" in output:
        errors.append("Error 4: Incorrect bit width for `rst`; ensure it is a single bit.")
    return "\n".join(errors)

def ensure_verilog_basics(code):
    lines = []
    if not code.strip().startswith('`timescale'):
        lines.append('`timescale 1ns / 1ps')
    if '`define RESET_VAL' not in code:
        lines.append('`define RESET_VAL 4\'b0000')
    lines.append(code)
    return '\n'.join(lines)

def main():
    # Dynamically load paths and configuration from config.json
    config_values, mixed_model_config, logfile = c.parse_args_and_config()
    design_file = os.path.abspath(config_values['prompt'])  # Dynamically load design file path
    testbench_file = os.path.abspath(config_values['testbench'])  # Dynamically load testbench path
    outdir = os.path.abspath(config_values['outdir'])
    os.makedirs(outdir, exist_ok=True)
    
    with open(design_file, 'r') as file:
        prompt = file.read()
    log_output("Debug", f"Loaded prompt: {prompt[:100]} ...")

    conversation = Conversation(log_file=logfile)
    conversation.add_message("system", "You are a Verilog code generator. Provide only valid Verilog code.")
    conversation.add_message("user", prompt)

    iterations = config_values['iterations']
    model_type = config_values['model_family']
    model_id = config_values['model_id']
    num_candidates = config_values['num_candidates']
    success = False

    start_time = time()
    
    for iteration in range(iterations):
        log_output("Iteration Start", f"Iteration {iteration + 1}/{iterations}")
        responses = vh.generate_verilog_responses(
            conversation,
            model_type=model_type,
            model_id=model_id,
            num_candidates=num_candidates
        )

        response = responses[0]
        log_output("Response Info", f"Full text: {response.full_text[:200]} ...")
        verilog_code = extract_verilog_code(response.parsed_text)

        if not verilog_code.strip():
            log_output("Debug", "No valid Verilog code found, using prompt as template...")
            verilog_code = ensure_verilog_basics(prompt)
        else:
            verilog_code = ensure_verilog_basics(verilog_code)

        if 'module' not in verilog_code:
            log_output("Error", "Generated code does not contain a module definition!")
            continue

        generated_design_path = os.path.join(outdir, f"generated_iter{iteration + 1}.v")
        log_output("File Save", f"Saving Verilog code to: {generated_design_path}")
        
        with open(generated_design_path, 'w') as design_out_file:
            design_out_file.write(verilog_code)

        backend = RivieraPROBackend(verilog_file=generated_design_path, testbench_file=testbench_file)  # Use RivieraPROBackend dynamically
        log_output("Compilation", "Starting compilation with Riviera-PRO...")
        compile_output = backend.compile()

        if compile_output and "0 Errors" in compile_output:
            log_output("Compilation", "Compilation successful. Proceeding with simulation...")
            return_code, stderr, stdout = backend.simulate()
            success = handle_simulation_output(return_code, stderr, stdout)
            if success:
                break
        else:
            log_output("Compilation Failed", f"Compilation failed. Iteration {iteration + 1}/{iterations}")
            if compile_output:
                error_feedback = parse_compilation_errors(compile_output)
                conversation.add_message("system", "Compilation error encountered.")
                conversation.add_message("user", error_feedback)

    end_time = time()
    log_output("Final", f"Generation Time: {end_time - start_time} seconds\nSuccess: {success}")

def handle_simulation_output(return_code, stderr, stdout):
    if return_code == 0 and not stderr:
        log_output("Simulation", "Simulation completed successfully!")
        if stdout:
            log_output("Simulation Output", stdout)
        return True
    else:
        log_output("Simulation Failed", "Simulation failed or had warnings.")
        if stderr:
            log_output("Error Output", stderr)
        return False

if __name__ == "__main__":
    main()
