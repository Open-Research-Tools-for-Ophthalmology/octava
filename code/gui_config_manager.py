import json
import os
from dataclasses import dataclass, asdict

@dataclass
class GUIConfig:
    """
    These are the default values for each user selectable.
    These values will be changed and saved to cache.json when the user changes them in the GUI.
    This does not include image_size mm as there are default values for each image type.
    """
    img_type: str = "Retina"  
    
    frangi_bool: int = 1
    frangi_min: int = 1
    frangi_max: int = 4

    jerman_bool: int = 0
    jerman_sigmas: str = "1, 2, 3, 4, 5"
    jerman_tau: float = 1.00

    onh_frangi_bool: int = 1
    onh_frangi_min: int = 1
    onh_frangi_max: int = 4
    onh_large_vessel_threshold_um: float = 60.0

    med_filt_bool: int = 0
    twig_size: int = 8
    kernel_size: int = 3
    prebinary_var: int = 0

class ConfigManager:
    def __init__(self, filename="cache.json"):
        self.filename = filename
        self.config = GUIConfig()  # starts with defaults
        self.load()
    
    def load(self):
        """Loads the config data from cache JSON file if it exists, otherwise uses default values."""
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                data = json.load(f)
                self.config = GUIConfig(**data)
    
    def save(self):
        """Saves the current config data to cache JSON file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(asdict(self.config), f, indent=4)
            
            print(f"Settings successfully saved to {self.filename}")
            
        except Exception as e:
            print(f"Error saving settings to {self.filename}: {e}")
    
    def update_config(self, **kwargs):
        """Updates the config JSON file and saves to file."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save()

# initialises config manager for persistent settings
manager = ConfigManager()