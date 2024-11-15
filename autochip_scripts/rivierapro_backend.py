import subprocess
import os


class RivieraPROBackend:
    def __init__(self, verilog_file, testbench_file):
        self.verilog_file = verilog_file
        self.testbench_file = testbench_file
        self.work_dir = "./work"

    def initialize_library(self):
        """Initialize a library directory for Riviera-PRO."""
        init_lib_cmd = f"vlib {self.work_dir}"
        try:
            print("Initializing library for Riviera-PRO...")
            result = subprocess.run(
                init_lib_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            print("Debug: Library initialized successfully.")
            return result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            print(f"Library initialization failed: {e}")
            return e.stdout + e.stderr if e.stdout or e.stderr else str(e)

    def list_compiled_units(self):
        """List compiled units in the Riviera-PRO library."""
        list_cmd = f"vdir {self.work_dir}"
        try:
            print("Checking compiled units in the library...")
            result = subprocess.run(
                list_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            print(f"Debug: Compiled units:\n{result.stdout}")
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error listing compiled units: {e}")
            return e.stdout + e.stderr if e.stdout or e.stderr else str(e)

    def compile(self):
        """Compile the Verilog design and testbench with Riviera-PRO."""
        self.initialize_library()
        compile_cmd = f"vlog -work {self.work_dir} {self.verilog_file} {self.testbench_file}"
        try:
            print("Compiling with Riviera-PRO...")
            result = subprocess.run(
                compile_cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
            print("Debug: Compilation successful.")
            return result.stdout + result.stderr
        except subprocess.CalledProcessError as e:
            print(f"Compilation failed: {e}")
            return e.stdout + e.stderr if e.stdout or e.stderr else str(e)

    def simulate(self, top_module="top_module"):
        """Simulate the design using Riviera-PRO."""
        # Verify if the top module exists in the compiled units
        compiled_units = self.list_compiled_units()
        if top_module not in compiled_units:
            error_message = f"Error: Top module '{top_module}' not found in compiled units."
            print(error_message)
            return False, None, error_message

        # Create a temporary `.do` file with the simulation commands
        do_file_path = "temp_simulation.do"
        try:
            with open(do_file_path, "w") as do_file:
                do_file.write(f"vsim -c work.{top_module}\n")
                do_file.write("run -all;\n")
                do_file.write("quit;\n")
            print(f"Debug: Simulation .do file created at {do_file_path}.")
        except Exception as e:
            print(f"Error: Failed to create simulation .do file: {e}")
            return False, None, str(e)

        # Run the simulation using the Riviera-PRO command line
        simulate_cmd = f"vsimsa -do {do_file_path}"
        try:
            print("Simulating with Riviera-PRO...")
            proc = subprocess.Popen(
                simulate_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )

            # Real-time output of simulation logs
            for line in iter(proc.stdout.readline, ""):
                print(line, end="")

            proc.wait(timeout=300)  # Set a timeout for the simulation
            if proc.returncode == 0:
                print("Debug: Simulation completed successfully.")
                return True, proc.stdout.read(), proc.stderr.read()
            else:
                print("Simulation encountered issues.")
                return False, proc.stdout.read(), proc.stderr.read()
        except subprocess.TimeoutExpired:
            print("Simulation timed out. Terminating...")
            proc.terminate()
            return False, None, "Simulation timed out."
        except subprocess.CalledProcessError as e:
            print(f"Simulation failed: {e}")
            return False, e.stdout, e.stderr
        finally:
            # Clean up the temporary `.do` file after simulation
            if os.path.exists(do_file_path):
                os.remove(do_file_path)
