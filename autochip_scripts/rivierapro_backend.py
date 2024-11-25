import subprocess
import os
import re
import shutil

class RivieraPROBackend:
   def __init__(self, verilog_file, testbench_file):
       self.verilog_file = verilog_file
       self.testbench_file = testbench_file
       self.work_dir = "./work"
       self.tb_module = self._get_testbench_module_name()

   def _get_testbench_module_name(self):
       """Extract the testbench module name from the testbench file."""
       try:
           with open(self.testbench_file, 'r') as f:
               content = f.read()
               # Look for the main testbench module that isn't stimulus_gen or reference_module
               for pattern in [
                   r'module\s+(\w+)\s*[;(]',
                   r'module\s+(\w+)\s*#\s*\([^)]*\)\s*[(;]',
                   r'module\s+(\w+)\s*\([^)]*\)\s*;'
               ]:
                   matches = re.finditer(pattern, content)
                   for match in matches:
                       module_name = match.group(1)
                       if module_name not in ['stimulus_gen', 'reference_module']:
                           return module_name
               return "tb"  # Default fallback
       except Exception as e:
           print(f"Warning: Could not extract testbench module name: {e}")
           return "tb"

   def initialize_library(self):
       """Initialize a library directory for Riviera-PRO."""
       if os.path.exists(self.work_dir):
           shutil.rmtree(self.work_dir)
           
       init_lib_cmd = f"vlib {self.work_dir}"
       try:
           print("Initializing library for Riviera-PRO...")
           result = subprocess.run(
               init_lib_cmd,
               shell=True,
               check=True,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               text=True
           )
           print("Debug: Library initialized successfully.")
           return result.stdout + result.stderr
       except subprocess.CalledProcessError as e:
           print(f"Library initialization failed: {e}")
           return e.stdout + e.stderr if e.stdout or e.stderr else str(e)

   def compile(self):
       """Compile the Verilog design and testbench with Riviera-PRO."""
       self.initialize_library()
       
       compile_cmd = f"vlog -work {self.work_dir} -dbg -sv2k12 {self.verilog_file} {self.testbench_file}"
       try:
           print(f"Debug: Running command: {compile_cmd}")
           result = subprocess.run(
               compile_cmd,
               shell=True,
               check=False,
               stdout=subprocess.PIPE,
               stderr=subprocess.PIPE,
               text=True,
               encoding='utf-8'
           )
           print(f"Debug: Command return code: {result.returncode}")
           print(f"Debug: Stdout: {result.stdout}")
           print(f"Debug: Stderr: {result.stderr}")
           
           if "SUCCESS" in result.stdout:
               print("Debug: Compilation successful.")
               return result.stdout + result.stderr
           else:
               print("Debug: Compilation had errors.")
               return result.stdout + result.stderr
       except Exception as e:
           print(f"Compilation failed with exception: {str(e)}")
           return str(e)

   def simulate(self):
    """Simulate the design using Riviera-PRO."""
    do_file_path = "temp_simulation.do"
    try:
        with open(do_file_path, "w") as do_file:
            do_file.write("onbreak {resume}\n")
            do_file.write("amap work work\n")
            do_file.write(f"asim +access +r {self.tb_module}\n")
            do_file.write("run -all;\n")
            do_file.write("quit;\n")
    except Exception as e:
        print(f"Error: Failed to create simulation .do file: {e}")
        return False, None, str(e)

    simulate_cmd = f"vsimsa -do {do_file_path}"
    try:
        print("Simulating with Riviera-PRO...")
        result = subprocess.run(
            simulate_cmd,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            stdout = result.stdout
            stderr = result.stderr

            # Parse total mismatches from output
            mismatch_pattern = r"Mismatches:\s*(\d+)\s*in\s*(\d+)\s*samples"
            match = re.search(mismatch_pattern, stdout)
            if match:
                total_mismatches = int(match.group(1))
                if total_mismatches == 0:
                    return 0, stderr, stdout  # Perfect match
                else:
                    return result.returncode, stdout, stderr  # Has mismatches
            return result.returncode, stdout, stderr
                
    except subprocess.TimeoutExpired:
        print("Simulation timed out after 300 seconds")
        return False, None, "Simulation timeout"
    except subprocess.CalledProcessError as e:
        print(f"Simulation failed: {e}")
        return False, e.stdout, e.stderr
    finally:
        if os.path.exists(do_file_path):
            os.remove(do_file_path)
