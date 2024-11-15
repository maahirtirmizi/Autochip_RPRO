**Prerequisites** 
1)	Python 3.6 or newer 
2)	pip for installing dependencies 
3)	Riviera Pro (licensed installation required)  
 
**Installation** 

1) Clone the repository to your local machine:
   git clone https://github.com/maahirtirmizi/Autochip_RPRO.git
   

2)	Set up a virtual environment (optional but recommended): 
  python3 -m venv venv
 venv\Scripts\activate 
 

3)	Install the required python packages: 
pip3 install -r requirements.txt 
 
 
4)	Activate API Key: 
 set OPENAI_API_KEY = "your API key"

  
5)	Copy the design and testbench files from verilogeval_prompts_tbs directory and paste it in autochip_scripts directory.
     
  
6)	Copy paths of both the files and paste it corresponding to ‘prompt’ and ‘testbench’ of config json respectively.  
 
 
7)	Go in the autochip_scripts directory in command prompt and run generate_verilog.py to start a compilation and simulation cycle.  
  
 
 
 
 
 
 
