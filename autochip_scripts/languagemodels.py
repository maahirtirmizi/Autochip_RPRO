import os
from abc import ABC, abstractmethod

# OPENAI
import openai

# ANTHROPIC
from anthropic import Anthropic
from anthropic import HUMAN_PROMPT, AI_PROMPT

# GEMINI
import google.generativeai as genai

# VERIGEN
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# HUMAN INPUT
import subprocess
import tempfile

# GENERAL AUTOCHIP
from conversation import Conversation
import verilog_handling as vh
import regex as re


# Abstract Large Language Model
class AbstractLLM(ABC):
    """Abstract Large Language Model."""

    @abstractmethod
    def generate(self, conversation: Conversation, num_candidates=1):
        """Generate a response based on the given conversation."""
        pass


class ChatGPT(AbstractLLM):
    """ChatGPT Large Language Model."""

    def __init__(self, model_id="gpt-3.5-turbo-16k"):
        openai.api_key = os.environ['OPENAI_API_KEY']
        self.model_id = model_id

    def generate(self, conversation: Conversation, num_candidates=1):
        messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation.get_messages()]
        response = openai.ChatCompletion.create(
            model=self.model_id,
            n=num_candidates,
            messages=messages,
        )
        return [choice.message['content'] for choice in response.choices]


class Claude(AbstractLLM):
    """Claude Large Language Model."""

    def __init__(self, model_id="claude-2"):
        self.anthropic = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
        self.model_id = model_id

    def generate(self, conversation: Conversation, num_candidates=1):
        messages = conversation.get_messages()
        system = next((item for item in messages if item["role"] == "system"), None)
        messages = [item for item in messages if item["role"] != "system"]

        responses = []
        for _ in range(num_candidates):
            completion = self.anthropic.completions.create(
                model=self.model_id,
                messages=messages,
                max_tokens=3000,
            )
            responses.append(completion.completion)
        return responses


class Gemini(AbstractLLM):
    """Gemini Large Language Model."""

    def __init__(self, model_id="gemini-pro"):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.model = genai.GenerativeModel(model_id)

    def generate(self, conversation: Conversation, num_candidates=1):
        conv_messages = conversation.get_messages()
        messages = [{"role": msg["role"], "parts": [msg["content"]]} for msg in conv_messages]

        responses = []
        for _ in range(num_candidates):
            response = self.model.generate_content(messages)
            responses.append(response.candidates[0].content.parts[0])
        return responses


class CodeLlama(AbstractLLM):
    """CodeLlama Large Language Model."""

    def __init__(self, model_id="codellama/CodeLlama-13b-hf"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", torch_dtype="auto")

    def generate(self, conversation: Conversation, num_candidates=1):
        prompt = self._format_prompt(conversation)
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")

        responses = []
        for _ in range(num_candidates):
            output = self.model.generate(
                inputs["input_ids"],
                max_new_tokens=3000,
                do_sample=True,
                top_p=0.9,
                temperature=0.1,
            )
            response = self.tokenizer.decode(output[0], skip_special_tokens=True)
            responses.append(response)
        return responses

    def _format_prompt(self, conversation: Conversation) -> str:
        messages = conversation.get_messages()
        prompt = ""
        for message in messages:
            if message['role'] == 'system':
                prompt += f"<<SYS>>\n{message['content']}\n<</SYS>>\n\n"
            elif message['role'] == 'user':
                prompt += f"<s>[INST] {message['content'].strip()} [/INST] "
            elif message['role'] == 'assistant':
                prompt += f"{message['content']}"
        return prompt


class HumanInput(AbstractLLM):
    """Human Input Large Language Model."""

    def generate(self, conversation: Conversation, num_candidates=1):
        editor = os.getenv('EDITOR', 'nano')
        initial_text = conversation.get_messages()[-1]['content']
        with tempfile.NamedTemporaryFile(suffix=".v") as tf:
            tf.write(initial_text.encode())
            tf.flush()
            subprocess.run([editor, tf.name])
            tf.seek(0)
            return tf.read().decode()


class RTLCoder(AbstractLLM):
    """RTLCoder Large Language Model."""

    def __init__(self, model_id="ishorn5/RTLCoder-Deepseek-v1.1"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", offload_folder="offload", torch_dtype=torch.float16)

    def generate(self, conversation: Conversation, num_candidates=1):
        prompt = self._format_prompt(conversation)
        inputs = self.tokenizer(prompt, return_tensors="pt").to("cuda")

        responses = []
        for _ in range(num_candidates):
            output = self.model.generate(
                inputs["input_ids"],
                max_new_tokens=3000,
                do_sample=True,
                top_p=0.9,
                temperature=0.1,
            )
            response = self.tokenizer.decode(output[0], skip_special_tokens=True)
            responses.append(response)
        return responses

    def _format_prompt(self, conversation: Conversation) -> str:
        messages = conversation.get_messages()
        prompt = ""
        for message in messages:
            if message['role'] == 'system':
                prompt += f"<<SYS>>\n{message['content']}\n<</SYS>>\n\n"
            elif message['role'] == 'user':
                prompt += f"<s>[INST] {message['content'].strip()} [/INST] "
            elif message['role'] == 'assistant':
                prompt += f"{message['content']}"
        return prompt


class LLMResponse:
    """Class to store the response from the LLM"""

    def __init__(self, iteration, response_num, full_text):
        self.iteration = iteration
        self.response_num = response_num
        self.full_text = full_text
        self.tokens = 0
        self.parsed_text = ""
        self.parsed_length = 0
        self.feedback = ""
        self.compiled = False
        self.rank = -3
        self.message = ""

    def set_parsed_text(self, parsed_text):
        self.parsed_text = parsed_text
        self.parsed_length = len(parsed_text)

    def parse_verilog(self):
        """Parse Verilog code from the response text."""
        # First try to find complete module definitions
        module_list = vh.find_verilog_modules(self.full_text)
        
        if module_list:
            self.parsed_text = "\n\n".join(module_list)
        else:
            # If no complete modules found, use the full text as is
            self.parsed_text = self.full_text
            
        # Add necessary headers if they're missing
        if not self.parsed_text.strip().startswith('`timescale'):
            self.parsed_text = '`timescale 1ns / 1ps\n\n' + self.parsed_text
            
        if '`define RESET_VAL' not in self.parsed_text:
            self.parsed_text = '`define RESET_VAL 4\'b0000\n\n' + self.parsed_text
            
        self.parsed_length = len(self.parsed_text)

    def calculate_rank(self, outdir, module, testbench):
        # Create output directory if it doesn't exist
        os.makedirs(outdir, exist_ok=True)
        
        # Save the parsed text to a file
        output_file = os.path.join(outdir, "response.v")
        with open(output_file, 'w') as f:
            f.write(self.parsed_text)
        
        try:
            # Try to compile and simulate
            return_code, stderr, stdout = vh.compile_and_simulate_verilog(output_file, testbench, self)
            
            if return_code == 0 and not stderr:
                self.rank = 1  # Success
                self.compiled = True
            else:
                self.rank = 0  # Failure
                self.compiled = False
                self.message = stderr if stderr else "Compilation failed"
                
        except Exception as e:
            self.rank = -1  # Error
            self.compiled = False
            self.message = str(e)