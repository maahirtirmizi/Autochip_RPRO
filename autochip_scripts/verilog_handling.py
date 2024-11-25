import subprocess
import languagemodels as lm
import conversation as cv
import os
import re
import tiktoken
import anthropic
from rivierapro_backend import RivieraPROBackend

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
   
   # If text contains only module internals, wrap it with the module declaration
   if not re.search(r'module\s+', cleaned_text, re.IGNORECASE) and ('assign' in cleaned_text or 'always' in cleaned_text):
       module_header = """
module top_module(
   input [2:0] vec, 
   output [2:0] outv,
   output o2,
   output o1,
   output o0
);
"""
       cleaned_text = module_header + cleaned_text
       if 'endmodule' not in cleaned_text:
           cleaned_text += "\nendmodule"
   
   # Try to find complete modules first
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

def analyze_simulation_results(stdout):
    """Analyze simulation output and extract mismatch information."""
    feedback = []
    current_mismatches = {}
    mismatch_count = float('inf')
    
    # Extract total mismatches
    total_match = re.search(r'Mismatches:\s*(\d+)\s*in\s*(\d+)', stdout)
    if total_match:
        mismatch_count = int(total_match.group(1))
        total_samples = int(total_match.group(2))
        feedback.append(f"\nDetected {mismatch_count} mismatches out of {total_samples} samples")
    
    # Extract per-signal mismatches and timing
    signal_pattern = r"Output '(\w+)' has (\d+) mismatches. First mismatch occurred at time (\d+)"
    for match in re.finditer(signal_pattern, stdout):
        signal, count, first_time = match.group(1), int(match.group(2)), int(match.group(3))
        current_mismatches[signal] = {"count": count, "first_time": first_time}
        if count > 0:
            feedback.append(f"- Signal {signal}: {count} mismatches, first occurred at time {first_time}")
    
    return feedback, current_mismatches, mismatch_count
def verilog_loop(design_prompt, module, testbench, max_iterations, model_type, model_id="", num_candidates=5, outdir="", log=None, mixed_model_config={}):
   if outdir != "":
       outdir = outdir + "/"
   conv = cv.Conversation(log_file=log)
   conv.add_message("system", """You are a Verilog code generator that learns from compilation and simulation feedback. 
   Follow these rules:
   1. Only use signals/ports defined in the module interface
   2. Follow the design requirements exactly as specified in the prompt
   3. Learn from any compilation errors
   4. Maintain the exact module interface as given""")
   conv.add_message("user", design_prompt)

   success = False
   timeout = False
   iterations = 0
   global_max_response = lm.LLMResponse(-3, -3, "")
   best_mismatches = float('inf')  # Track best result
   best_output_mismatches = {}  # Track best performance per signal
   best_code = None  # Store best code

   while not (success or timeout):
       # If we have successful compilation from previous iteration, include it
       if best_code and best_mismatches < float('inf'):
           feedback = [
               f"\nPrevious iteration achieved {best_mismatches} mismatches.",
               "Analysis of best attempt so far:"
           ]
           
           # Add timing-based analysis
           early_failures = [sig for sig, data in best_output_mismatches.items() 
                           if data['first_time'] < 100 and data['count'] > 0]
           if early_failures:
               feedback.append(f"Signals failing early (check initialization): {', '.join(early_failures)}")
           
           late_failures = [sig for sig, data in best_output_mismatches.items() 
                          if data['first_time'] >= 100 and data['count'] > 0]
           if late_failures:
               feedback.append(f"Signals failing during operation: {', '.join(late_failures)}")
           
           conv.add_message("user", "\n".join(feedback))

       if mixed_model_config:
           model_type, model_id = get_iteration_model(iterations, mixed_model_config)

       responses = generate_verilog_responses(conv, model_type, model_id, num_candidates=num_candidates)
       
       for idx, response in enumerate(responses):
           response_outdir = os.path.join(outdir, f"iter{iterations}/response{idx}/")
           os.makedirs(response_outdir, exist_ok=True)
           response.parse_verilog()

           backend = RivieraPROBackend(
               verilog_file=os.path.join(response_outdir, f"{module}.sv"),
               testbench_file=testbench
           )

           compile_output = backend.compile()
           if "0 Errors" in compile_output:
               return_code, stderr, stdout = backend.simulate()
               
               if stdout:
                   feedback, current_mismatches, mismatch_count = analyze_simulation_results(stdout)
                   
                   # Check for improvement
                   if mismatch_count < best_mismatches:
                       improvement_msg = [
                           f"\nImprovement found: {best_mismatches} -> {mismatch_count} mismatches",
                           "Changes in signal behavior:"
                       ]
                       
                       for signal, data in current_mismatches.items():
                           prev_data = best_output_mismatches.get(signal, {'count': float('inf')})
                           if data['count'] < prev_data['count']:
                               improvement_msg.append(
                                   f"- {signal} improved: {prev_data['count']} -> {data['count']} mismatches"
                               )
                       
                       feedback.extend(improvement_msg)
                       best_mismatches = mismatch_count
                       best_code = response.parsed_text
                       best_output_mismatches = current_mismatches
                       
                       if mismatch_count == 0:
                           print("Perfect match achieved - stopping iterations")
                           return global_max_response
                       
                       response.rank = 1
                       global_max_response = response
                   else:
                       response.rank = -1
                   
                   response.message = "\n".join(feedback)
           else:
               response.rank = -1
               response.message = compile_output or "Compilation errors occurred."

           # Save logs for each iteration
           with open(os.path.join(response_outdir, "log.txt"), 'w') as file:
               file.write('\n'.join(str(i) for i in conv.get_messages()))
               file.write(format_message("assistant", response.full_text))
               file.write('\n\n Iteration rank: ' + str(response.rank) + '\n')
               file.write(f"\n Model: {model_id}")
               if current_mismatches:
                   file.write("\n\nMismatch Analysis:\n")
                   for signal, data in current_mismatches.items():
                       file.write(f"{signal}: {data['count']} mismatches (first at {data['first_time']})\n")

       if not success:
           max_rank_response = max(responses, key=lambda resp: (resp.rank, -resp.parsed_length))
           
           conv.add_message("assistant", max_rank_response.parsed_text)
           conv.remove_message(2)
           conv.remove_message(2)
           conv.add_message("user", max_rank_response.message)

       timeout = iterations >= max_iterations
       iterations += 1

   return global_max_response
