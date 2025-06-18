import platform
import json
import os
from pathlib import Path


CFG_FILE = "config.json"
APP_NAME = "Pyshi"


CFG_KENSHI_DIR = "KENSHI_DIR"


class Config:
    def __init__(self):
        self._config_path = self.get_config_file_path(APP_NAME, CFG_FILE)
        self._config = self._load_config()

    @property
    def kenshi_dir(self):
        """
        Get the Kenshi directory from the configuration.
        If not set, return None.
        """
        return self._config.get(CFG_KENSHI_DIR, None)
    
    @kenshi_dir.setter
    def kenshi_dir(self, value):
        """
        Set the Kenshi directory in the configuration.
        """
        if not isinstance(value, str):
            raise ValueError("Kenshi directory must be a string.")
        self._config[CFG_KENSHI_DIR] = value
        self._save_config()

    @staticmethod
    def get_config_dir(app_name):
        """
        Get the configuration directory based on the operating system.
        """
        if platform.system() == "Windows":
            config_dir = Path.home() / "AppData" / "LocalLow" / app_name
        elif platform.system() == "Linux":
            # For Linux, we can use XDG Base Directory Specification
            config_dir = Path.home() / ".config" / app_name
        elif platform.system() == "Darwin":  # macOS
            # For macOS, we can use the Application Support directory
            config_dir = Path.home() / "Library" / "Application Support" / app_name
        else:
            raise NotImplementedError("Unsupported operating system for configuration file path.")
        return config_dir
    
    @staticmethod
    def get_config_file_path(app_name, config_filename):
        """ Get the full path to the configuration file."""
        config_dir = Config.get_config_dir(app_name)
        return config_dir / config_filename
    
    def _load_config(self):
        """
        Load the configuration from the file, creating it if it doesn't exist.
        """
        config_path = self._config_path
        if not config_path.exists():
            # Create the directory if it doesn't exist
            config_path.parent.mkdir(parents=True, exist_ok=True)
            # Create an empty config file
            with open(config_path, 'w') as f:
                json.dump({}, f, indent=4)
        
        with open(config_path, 'r') as f:
            return json.load(f)
        
    def _save_config(self):
        """
        Save the current configuration to the file.
        """
        with open(self._config_path, 'w') as f:
            json.dump(self._config, f, indent=4)

        
    
if __name__ == "__main__":
    config = Config()
    print(f"Config loaded from: {config._config_path}")
    print("Current configuration:", config._config)