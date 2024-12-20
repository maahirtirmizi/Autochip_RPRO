# **AutoChip_RPRO Setup Guide**

## **Prerequisites**
1. **Python**: Version 3.6 or newer installed on your system.
2. **Riviera Pro**: Licensed installation required for simulations.
3. **OpenAI API Key**: Necessary for generating Verilog code.

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
- Update the `"prompt"` field to the design file path.
- Update the `"testbench"` field to the testbench file path.
- Use **forward slashes** for all file paths.
- Adjust the `"iterations"` field to control the number of iterations during the generation process. It should look like this:
  ```json
  {
    "general": {
        "prompt": "C:/Users/tirmi/autochip_rpro/AutoChip/autochip_scripts/fsm_onehot.sv",
        "name": "fsm_onehot.sv",
        "testbench": "C:/Users/tirmi/autochip_rpro/AutoChip/autochip_scripts/fsm_onehot_tb.sv",
        "model_family": "ChatGPT",
        "model_id": "gpt-4",
        "num_candidates": 2,
        "iterations": 4,
        "outdir": "test_outdir",
        "log": "log.txt",
        "mixed-models": false,
        "simulator": "RivieraPRO"
    }
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

## **10. Best Practices**
- Always delete the `work` directory in the project root before replacing the design and testbench files to avoid errors during compilation or simulation.
- Double-check the file paths in the `config.json` file for accuracy, ensuring forward slashes are used.
- The more detailed and descriptive the design prompt is, the better the chances are for compilation and simulation to be successful in fewer iterations.

---

## **Support**  
For further assistance or troubleshooting, feel free to reach out at:  
📧 **Email**: tirmizimaahir@gmail.com  

For Riviera Pro-related issues, consult the official documentation or contact Aldec support.

