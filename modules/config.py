import json

class Config:
    def __init__(self):
        self.config_file = '../settings/config.json'

    def load(self):
        with open(self.config_file, 'r') as f:
            return json.load(f) 