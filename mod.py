from pathlib import Path

# .save, .platoon, .zone
FILE_TYPE_DATA = 15

# .mod
FILE_TYPE_MOD = 16

# also a mod?
FILE_TYPE_MMOD = 17


class Mod:
    def __init__(self, path):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Mod path does not exist: {self.path}")
        
        self.name: str = ""
        self.version: str = ""
        self.author: str = ""
        self.description: str = ""
        self.mod_id: int = -1

        self._stream: bytes = b""
        with open(self.path, 'rb') as f:
            self._stream = f.read()

        self._parse_mod_info()

    def __str__(self):
        return (f"Mod ID: {self.mod_id}\n"
                f"Name: {self.name}\n"
                f"Version: {self.version}\n"
                f"Author: {self.author}\n"
                f"Description: {self.description}")
    
    def __repr__(self):
        return f"Mod({self.mod_id}, '{self.name}', '{self.version}', '{self.author}')"
    
    def _parse_mod_info(self):
        """Parse the mod information from the binary stream."""
        if not self._stream:
            raise ValueError("Mod stream is empty")
        # read type
        # read header data
        
    
if __name__ == "__main__":
    # Example usage
    mod_path = "./example_mods/locals/0_Canine_Variation/0_Canine_Variation.mod"
    try:
        mod = Mod(mod_path)
        print(mod)
    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")