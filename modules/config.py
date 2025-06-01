import json
import os

class Config:
    def __init__(self):
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_file = os.path.join(self.base_path, 'settings', 'config.json')

    def load(self):
        with open(self.config_file, 'r') as f:
            return json.load(f) 

    def get_prompt(self):
        prompt_file = os.path.join(self.base_path, 'settings', 'prompt.txt')
        with open(prompt_file, 'r') as f:
            return f.read()