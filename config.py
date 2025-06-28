import platform
import json
import os
from pathlib import Path


CFG_FILE = "config.json"


APP_NAME = "KenPy"
VERSION = "1.0.1"

# I know I made it MIT licensed, but whatever, anyone can change it if they make their own version
AUTHOR = "Miroslav Jurek (Agamenton)"
APP_TITLE = f"{APP_NAME} - Kenshi Mod Manager - v{VERSION} by {AUTHOR}"


CFG_KENSHI_DIR = "KENSHI_DIR"
CFG_DARK_MODE = "DARK_MODE"
CFG_WINDOW_WIDTH = "WINDOW_WIDTH"
CFG_WINDOW_HEIGHT = "WINDOW_HEIGHT"

WINDOW_DEFAULT_WIDTH = 1200
WINDOW_DEFAULT_HEIGHT = 600

WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 400

_default_config = {
    CFG_KENSHI_DIR: "",  # Kenshi directory path
    CFG_DARK_MODE: True,   # Dark mode setting
    CFG_WINDOW_WIDTH: WINDOW_DEFAULT_WIDTH,  # Default window width
    CFG_WINDOW_HEIGHT: WINDOW_DEFAULT_HEIGHT,  # Default window height
}

class Config:
    def __new__(cls):
        """
        Ensure that Config is a singleton.
        """
        if not hasattr(cls, 'instance'):
            cls.instance = super(Config, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        """
        Initialize the Config instance.
        Load the configuration from the file or create a new one if it doesn't exist.
        """
        self._config_path = self.get_config_file_path(APP_NAME, CFG_FILE)
        self._config = self._load_config()
        self.instance = self  # Ensure the instance is set for singleton access

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

    @property
    def dark_mode(self):
        """
        Get the dark mode setting from the configuration.
        If not set, return True.
        """
        return self._config.get(CFG_DARK_MODE, True)
    
    @dark_mode.setter
    def dark_mode(self, value):
        """
        Set the dark mode setting in the configuration.
        """
        if not isinstance(value, bool):
            raise ValueError("Dark mode must be a boolean value.")
        self._config[CFG_DARK_MODE] = value
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
    
    @property
    def window_width(self):
        """
        Get the window width from the configuration.
        If not set, return the default width.
        """
        return self._config.get(CFG_WINDOW_WIDTH, WINDOW_DEFAULT_WIDTH)
    
    @window_width.setter
    def window_width(self, value):
        """
        Set the window width in the configuration.
        """
        if isinstance(value, int) and value >= WINDOW_MIN_WIDTH:
            self._config[CFG_WINDOW_WIDTH] = value

    @property
    def window_height(self):
        """
        Get the window height from the configuration.
        If not set, return the default height.
        """
        return self._config.get(CFG_WINDOW_HEIGHT, WINDOW_DEFAULT_HEIGHT)
    
    @window_height.setter
    def window_height(self, value):
        """
        Set the window height in the configuration.
        """
        if isinstance(value, int) and value >= WINDOW_MIN_HEIGHT:
            self._config[CFG_WINDOW_HEIGHT] = value
    
    def save_win_size(self):
        """
        Save the current window size to the configuration.
        """
        self._save_config()
    
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
                json.dump(_default_config, f, indent=4)
        
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