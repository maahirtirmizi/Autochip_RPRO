Here's the revised content including step 9:

---

# **AutoChip Setup Guide**

## **Prerequisites**
1. **Python**: Version 3.6 or newer installed on your system.
2. **pip**: Installed for managing Python dependencies.
3. **Riviera Pro**: Licensed installation required for simulations.
4. **OpenAI API Key**: Necessary for generating Verilog code.

---

## **Installation Steps**

### 1. Clone the Repository
Run the following command to download the repository to your local machine:
```bash
git clone https://github.com/maahirtirmizi/Autochip_RPRO.git
```

### 2. Set Up a Virtual Environment (Optional but Recommended)
Create and activate a virtual environment to isolate project dependencies:
```bash
python3 -m venv venv
venv\Scripts\activate  # On Windows
```

### 3. Install Required Python Packages
Use `pip` to install the required dependencies:
```bash
pip3 install -r requirements.txt
```

### 4. Activate OpenAI API Key
Set your API key for generating Verilog code:
```bash
set OPENAI_API_KEY="your API key"
```

### 5. Add Design and Testbench Files
Paste the appropriate **design** and **testbench** files into the `autochip_scripts` directory.

### 6. Update Configuration File
Edit the `config.json` file in the `autochip_scripts` directory:
- Use **forward slashes** for all file paths.
- Update the `"prompt"` field to the design file path.
- Update the `"testbench"` field to the testbench file path.
- Adjust the `"max_iterations"` field to control the number of iterations during the generation process. For example:
  ```json
  {
    "prompt": "C:/path_to_file/design_file.sv",
    "testbench": "C:/path_to_file/testbench_file.sv",
    "max_iterations": 3,
    ...
  }
  ```

### 7. Navigate to AutoChip Scripts Directory
Change to the `autochip_scripts` directory using the command prompt:
```bash
cd autochip_scripts
```

### 8. Run the Generate Verilog Script
Start the compilation and simulation process by executing:
```bash
python generate_verilog.py
```

### 9. Review Logs and Generated Code
- Check the **log output** during the execution for progress updates.
- View the **generated files** for each iteration inside the `test_outdir` directory. This includes:
  - Logs for each iteration.
  - Generated Verilog code for both the design and testbench files.

---

## **Support**
For further assistance or troubleshooting, please contact me at tirmizimaahir@gmail.com.
