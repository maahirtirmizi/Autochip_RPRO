import subprocess
import languagemodels as lm
import conversation as cv
import os
import re
import tiktoken
import anthropic
from rivierapro_backend import RivieraPROBackend  # Updated import

def format_message(role, content):
    return f"\n{{role : '{role}', content : '{content}'}}"

def clean_generated_verilog(code):
    """Clean up generated Verilog code by removing markdown artifacts and formatting."""
    code = re.sub(r'```verilog|```', '', code)
    code = re.sub(r"Here's .*?:\s*", '', code)
    code = re.sub(r"Here is .*?:\s*", '', code)
    code = re.sub(r'\n\s*\n', '\n\n', code)
    return code.strip()

def sanitize_verilog_code(code):
    """Clean and format Verilog code."""
    code = clean_generated_verilog(code)
    if not code.strip().startswith('`timescale'):
        code = '`timescale 1ns / 1ps\n\n' + code
    lines, indent_level = [], 0
    for line in code.split('\n'):
        line = line.strip()
        if line:
            if any(keyword in line for keyword in ['end', 'endmodule', 'endcase']):
                indent_level = max(0, indent_level - 1)
            lines.append('    ' * indent_level + line)
            if any(keyword in line for keyword in ['begin', 'case', 'module']):
                indent_level += 1
    return '\n'.join(lines)

def find_verilog_modules(text):
    cleaned_text = clean_generated_verilog(text)
    module_pattern = r'(?:^|\n)\s*(?:`timescale\s+[^`\n]*\s*\n)?\s*(?:`define\s+[^`\n]*\s*\n)*\s*module\s+[\w\\_]+\s*(?:#\s*\([^)]*\))?\s*\([^)]*\)\s*;.*?endmodule'
    matches = re.findall(module_pattern, cleaned_text, re.DOTALL | re.MULTILINE)
    if not matches:
        module_pattern = r'module\s+[\w\\_]+\s*(?:#\s*\([^)]*\))?\s*\([^)]*\)\s*;.*?endmodule'
        matches = re.findall(module_pattern, cleaned_text, re.DOTALL)
    return [match.strip() for match in matches]

def write_code_blocks_to_file(markdown_string, module_name, filename):
    code_blocks = find_verilog_modules(markdown_string)
    if not code_blocks:
        print("No valid Verilog modules found in response")
        return False
    try:
        with open(filename, 'w') as file:
            for code_block in code_blocks:
                cleaned_code = sanitize_verilog_code(code_block)
                if '`timescale' not in cleaned_code:
                    file.write('`timescale 1ns / 1ps\n\n')
                if '`define RESET_VAL' not in cleaned_code:
                    file.write('`define RESET_VAL 4\'b0000\n\n')
                file.write(cleaned_code)
                file.write('\n\n')
        return True
    except Exception as e:
        print(f"Error writing to file: {e}")
        return False

def analyze_compilation_errors(compile_output):
    """Analyze compilation output to identify common Verilog syntax issues."""
    issues = {
        'missing_endmodule': False,
        'undefined_macros': set(),
        'syntax_errors': [],
        'timing_issues': False,
        'macro_name_errors': False
    }
    if compile_output:
        lines = compile_output.split('\n')
        for line in lines:
            if "module/macromodule...endmodule pair(s) mismatch" in line:
                issues['missing_endmodule'] = True
            elif "Macro" in line and "is not defined" in line:
                macro_name = line.split("Macro")[1].split("is not defined")[0].strip()
                issues['undefined_macros'].add(macro_name)
            elif "Name of macro is not specified" in line:
                issues['macro_name_errors'] = True
            elif "Syntax error" in line:
                issues['syntax_errors'].append(line)
            elif "timescale" in line:
                issues['timing_issues'] = True
    return issues

def generate_verilog_responses(conv, model_type, model_id="", num_candidates=1):
    if model_type == "ChatGPT":
        model = lm.ChatGPT(model_id)
    elif model_type == "Claude":
        model = lm.Claude(model_id)
    elif model_type == "Gemini":
        model = lm.Gemini(model_id)
    elif model_type == "Human":
        model = lm.HumanInput()
    else:
        raise ValueError("Invalid model type")

    response_texts = model.generate(conversation=conv, num_candidates=num_candidates)
    responses = [lm.LLMResponse(0, idx, response_text) for idx, response_text in enumerate(response_texts)]
    for response in responses:
        response.parse_verilog()
    return responses

def get_iteration_model(iteration, mixed_model_config):
    sorted_models = sorted(mixed_model_config.values(), key=lambda x: x['start_iteration'], reverse=True)
    family, model_id = None, None
    for model_info in sorted_models:
        if iteration >= model_info['start_iteration']:
            family = model_info['model_family']
            model_id = model_info['model_id']
            break
    return family, model_id

def verilog_loop(design_prompt, module, testbench, max_iterations, model_type, model_id="", num_candidates=5, outdir="", log=None, mixed_model_config={}):
    if outdir != "":
        outdir = outdir + "/"
    conv = cv.Conversation(log_file=log)
    conv.add_message("system", "You are an autocomplete engine for Verilog code. Format your response as Verilog code.")
    conv.add_message("user", design_prompt)

    success, timeout, iterations = False, False, 0
    global_max_response = lm.LLMResponse(-3, -3, "")

    while not (success or timeout):
        if mixed_model_config:
            model_type, model_id = get_iteration_model(iterations, mixed_model_config)

        responses = generate_verilog_responses(conv, model_type, model_id, num_candidates=num_candidates)
        
        for idx, response in enumerate(responses):
            response_outdir = os.path.join(outdir, f"iter{iterations}/response{idx}/")
            os.makedirs(response_outdir, exist_ok=True)
            response.parse_verilog()

            # Integrate with Riviera-PRO Backend
            backend = RivieraPROBackend(  # Updated backend
                verilog_file=os.path.join(response_outdir, f"{module}.sv"),
                testbench_file=testbench
            )

            compile_output = backend.compile()
            if "0 Errors" in compile_output:
                return_code, stderr, stdout = backend.simulate()
                if return_code == 0 and not stderr:
                    success = True
                    response.rank = 1  # Successful rank
                else:
                    response.rank = -1  # Simulation failed
                    response.message = stderr or "Simulation errors occurred."
            else:
                response.rank = -1  # Compilation failed
                response.message = compile_output or "Compilation errors occurred."

            # Save logs for each iteration
            with open(os.path.join(response_outdir, "log.txt"), 'w') as file:
                file.write('\n'.join(str(i) for i in conv.get_messages()))
                file.write(format_message("assistant", response.full_text))
                file.write('\n\n Iteration rank: ' + str(response.rank) + '\n')
                file.write(f"\n Model: {model_id}")

        max_rank_response = max(responses, key=lambda resp: (resp.rank, -resp.parsed_length))
        if max_rank_response.rank > global_max_response.rank:
            global_max_response = max_rank_response

        conv.add_message("assistant", max_rank_response.parsed_text)
        success = max_rank_response.rank == 1

        if not success:
            conv.remove_message(2)
            conv.remove_message(2)
            conv.add_message("user", max_rank_response.message)

        timeout = iterations >= max_iterations
        iterations += 1

    return global_max_response  
