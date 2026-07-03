import json
import os
from dataclasses import dataclass, asdict

@dataclass
class GUIConfig:
    img_type: str = "Retina"  # default value

class ConfigManager:
    def __init__(self, filename="cache.json"):
        self.filename = filename
        self.config = GUIConfig()  # starts with defaults
        self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.config = GUIConfig(**data)
    
    def save(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(asdict(self.config), f, indent=4)
            
            print(f"Settings successfully saved to {self.filename}")
            
        except Exception as e:
            print(f"Error saving settings to {self.filename}: {e}")
    
    def update_config(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()