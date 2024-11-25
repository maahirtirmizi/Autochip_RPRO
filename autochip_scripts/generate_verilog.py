import config_handler as c
import verilog_handling as vh
from rivierapro_backend import RivieraPROBackend
from conversation import Conversation
import os
from time import time
import re
import shutil

def log_output(stage, details):
    print(f"\n{stage}:")
    print(details)
    print("=" * 50)

def extract_interface_from_prompt(prompt_file):
    try:
        with open(prompt_file, 'r') as f:
            content = f.read()
            match = re.search(r'module\s+top_module\s*\(([\s\S]*?)\);', content)
            if match:
                return match.group(1).strip()
    except Exception as e:
        print(f"Warning: Could not extract interface: {e}")
    return None

def clean_comments_and_text(text):
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line and not any(x in line.lower() for x in [
            'i apologize', 'here is', 'this code', 'explanation:', 'note:',
            'sorry', 'implementation', 'begin by']):
            lines.append(line)
    return '\n'.join(lines)

def extract_implementation(text):
    """Extract implementation part between module declaration and endmodule."""
    text = re.sub(r'module\s+\w+\s*\([^)]*\)\s*;', '', text)
    text = re.sub(r'endmodule.*$', '', text)
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text

def extract_verilog_code(text, interface=None):
    cleaned_text = re.sub(r'```verilog|```', '', text)
    cleaned_text = re.sub(r"Here's .*?:\s*", '', cleaned_text)
    cleaned_text = re.sub(r"Here is .*?:\s*", '', cleaned_text)
    cleaned_text = clean_comments_and_text(cleaned_text)
    
    if interface:
        template = f"""
`timescale 1ns / 1ps
`define RESET_VAL 4'b0000

module top_module(
{interface}
);
"""
        implementation = extract_implementation(cleaned_text)
        if implementation:
            return template + implementation + "\nendmodule"
    return cleaned_text

def ensure_verilog_basics(code):
    directives = []
    module_code = []
    lines = code.split('\n')
    
    for line in lines:
        line = line.strip()
        if line.startswith('`'):
            if line not in directives:
                directives.append(line)
        else:
            module_code.append(line)
    
    result = '\n'.join(directives)
    result += '\n\n' + '\n'.join(line for line in module_code if line)
    result = '\n'.join(line.rstrip() for line in result.split('\n'))
    return result

def handle_simulation_output(return_code, stderr, stdout):
    if stdout:
        log_output("Simulation", "Simulation completed")
        
        important_lines = []
        mismatch_count = float('inf')
        success = False
        
        for line in stdout.split('\n'):
            if any(x in line for x in ['Hint:', 'Mismatches:', 'Total']):
                important_lines.append(line.strip())
                match = re.search(r'Mismatches:\s*(\d+)\s*in', line)
                if match:
                    mismatch_count = int(match.group(1))
                    if mismatch_count == 0:
                        success = True

        if important_lines:
            log_output("Simulation Results", "\n".join(important_lines))

        if success:
            log_output("Simulation Status", "Simulation completed successfully - NO MISMATCHES!")
            return True, 0
        else:
            log_output("Simulation Status", f"Simulation completed with {mismatch_count} mismatches")
            return False, mismatch_count
    else:
        log_output("Simulation Status", "Simulation failed or produced no output")
        if stderr:
            log_output("Error Details", stderr)
        return False, float('inf')

def main():
    if os.path.exists("work"):
        shutil.rmtree("work")
    if os.path.exists("test_outdir"):
        shutil.rmtree("test_outdir")
    
    config_values, mixed_model_config, logfile = c.parse_args_and_config()
    design_file = os.path.abspath(config_values['prompt'])
    testbench_file = os.path.abspath(config_values['testbench'])
    outdir = os.path.abspath(config_values['outdir'])
    os.makedirs(outdir, exist_ok=True)
    
    interface = extract_interface_from_prompt(design_file)
    
    with open(design_file, 'r') as file:
        prompt = file.read()
    log_output("Debug", f"Loaded prompt: {prompt[:100]} ...")

    conversation = Conversation(log_file=logfile)
    conversation.add_message("system", """You are a Verilog code generator that learns from feedback and previous attempts.

GENERAL RULES:
1. Carefully analyze and follow ALL design requirements from the prompt
2. Maintain exact module interface (ports, signals, parameters) as specified
3. Choose appropriate Verilog constructs based on the design type:
   - Combinational logic: assign statements
   - Sequential logic: always blocks with proper sensitivity lists
   - State machines: recommended state encoding and transitions
   - Arithmetic: appropriate operators and bit widths

LEARNING BEHAVIOR:
1. Study compilation errors when they occur:
   - Fix signal/port declarations
   - Correct syntax issues
   - Resolve timing and logic conflicts
2. Analyze simulation mismatches:
   - Identify which outputs are incorrect
   - Understand timing of first mismatches
   - Fix logic equations accordingly

IMPROVEMENT STRATEGY:
1. Keep working parts from previous iterations
2. Focus on fixing specifically identified issues
3. Maintain correct functionality that was previously achieved
4. Build upon successful approaches
5. Follow test requirements and verification conditions

REQUIREMENTS CHECKLIST:
1. Verify all input signals are used correctly
2. Ensure all outputs are properly driven
3. Follow specified timing and logic requirements
4. Handle all corner cases and special conditions
5. Implement proper error checking if required""")
    conversation.add_message("user", prompt)

    iterations = config_values['iterations']
    model_type = config_values['model_family']
    model_id = config_values['model_id']
    num_candidates = config_values['num_candidates']
    success = False
    iteration_completed = 0
    best_code = None
    best_mismatches = float('inf')
    start_time = time()
    
    for iteration in range(iterations):
        iteration_completed = iteration + 1
        log_output("Iteration Start", f"Iteration {iteration + 1}/{iterations}")
        
        try:
            if best_code and best_mismatches < float('inf'):
                log_output("Using Previous Best", f"Previous best code had {best_mismatches} mismatches")
                verilog_code = best_code
            else:
                responses = vh.generate_verilog_responses(
                    conversation,
                    model_type=model_type,
                    model_id=model_id,
                    num_candidates=num_candidates
                )
                response = responses[0]
                log_output("Response Info", f"Full text: {response.full_text[:200]} ...")
                verilog_code = extract_verilog_code(response.parsed_text, interface)
                verilog_code = ensure_verilog_basics(verilog_code)

            log_output("Code for Iteration", verilog_code)
            generated_design_path = os.path.join(outdir, f"generated_iter{iteration + 1}.v")
            
            with open(generated_design_path, 'w') as design_out_file:
                design_out_file.write(verilog_code)

            backend = RivieraPROBackend(verilog_file=generated_design_path, testbench_file=testbench_file)
            compile_output = backend.compile()

            if compile_output and "SUCCESS" in compile_output:
                return_code, stderr, stdout = backend.simulate()
                success, mismatch_count = handle_simulation_output(return_code, stderr, stdout)
                
                if stdout and ("Total mismatched samples is 0" in stdout or "Mismatches: 0 in" in stdout):
                    success = True
                    mismatch_count = 0
                    log_output("Simulation Status", "Simulation completed successfully with no mismatches")
                
                if mismatch_count < best_mismatches:
                    best_mismatches = mismatch_count
                    best_code = verilog_code
                    log_output("New Best", f"Found better code with {mismatch_count} mismatches")
                
                if mismatch_count == 0:
                    success = True
                    log_output("Process Status", "Design verified successfully with 0 mismatches - stopping iterations")
                    break
                    
            else:
                if compile_output:
                    error_analysis = []
                    if 'undeclared identifier' in compile_output:
                        error_analysis.append("- Port/Signal Issues: Ensure all signals are properly declared")
                    if 'not a valid left-hand side' in compile_output:
                        error_analysis.append("- Assignment Issues: Check assignment types and target signals")
                    if 'Syntax error' in compile_output:
                        error_analysis.append("- Syntax Issues: Verify Verilog syntax and statements")
                    
                    error_feedback = f"""Compilation failed. Analysis:
{chr(10).join(error_analysis)}

Original compilation errors:
{compile_output}

Previous best approach had {best_mismatches} mismatches.
{f'Best working code so far:{chr(10)}{best_code}' if best_code else 'No working solution yet'}
                    """
                    conversation.add_message("system", "Analyze and fix these compilation errors")
                    conversation.add_message("user", error_feedback)

        except Exception as e:
            log_output("Error", f"Iteration failed with error: {str(e)}")
            continue

    end_time = time()
    total_time = end_time - start_time
    
    if success:
        log_output("Final Results", f"""
Simulation SUCCESSFUL:
- Completed in {iteration_completed} iterations
- Total time: {total_time:.2f} seconds
- Final mismatch count: 0""")
    else:
        log_output("Final Results", f"""
Simulation FAILED:
- Attempted all {iterations} iterations
- Total time: {total_time:.2f} seconds
- Best mismatch count: {best_mismatches}""")

    log_output("Final", f"Generation Time: {total_time} seconds\nSuccess: {success}")

if __name__ == "__main__":
    main()
