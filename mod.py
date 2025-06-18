from pathlib import Path
from datetime import datetime

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
        
        self.name: str = self.path.stem
        self.version: str = ""
        self.author: str = ""
        self.description: str = ""
        self.requires: list[str] = []
        self.references: list[str] = []
        try:
            self.date_added: datetime = datetime.fromtimestamp(self.path.stat().st_birthtime)   # may 
        except AttributeError:
            self.date_added = datetime.fromtimestamp(self.path.stat().st_mtime)

        self._stream: bytes = b""
        self._head = 0
        with open(self.path, 'rb') as f:
            self._stream = f.read()

        self._parse_mod_info()

    def __str__(self):
        return (f"Name: {self.name}\n"
                f"Date Added: {self.date_added.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Version: {self.version}\n"
                f"Author: {self.author}\n"
                f"Description: {self.description}")
    
    def __repr__(self):
        return f"Mod('{self.name}', '{self.version}', '{self.author}')"
    
    def _parse_mod_info(self):
        """Parse the mod information from the binary stream."""
        if not self._stream:
            raise ValueError("Mod stream is empty")
        
        ftype = self.read_32int()
        if ftype != FILE_TYPE_MOD and ftype != FILE_TYPE_MMOD:
            raise ValueError(f"Invalid file type: {ftype}, expected {FILE_TYPE_MOD} or {FILE_TYPE_MMOD}")
        
        if ftype == FILE_TYPE_MMOD:
            self.read_32int()   # merged mods also contain another 32-bit integer to tell us where the header ends
        
        self.version = self.read_32int()
        self.author = self.read_string()
        self.description = self.read_string()
        self.requires = self.read_strings()
        self.references = self.read_strings()

    def read_32int(self):
        start = self._head
        self._head += 4
        return int.from_bytes(self._stream[start:self._head], 'little')
    
    def read_string(self):
        length = self.read_32int()
        if length <= 0:
            return ""
        start = self._head
        self._head += length
        return self._stream[start:self._head].decode('utf-8', errors='ignore')
    
    def read_strings(self):
        strings = self.read_string().split(',')
        # Remove empty strings
        return [s for s in strings if s]


    
if __name__ == "__main__":
    # tests
    example_mods_path = "./example_mods"
    # find all .mod files recursively in the example_mods directory
    all_mod_files = list(Path(example_mods_path).rglob("*.mod"))
    for mod_path in all_mod_files:
        print("**" * 20)
        print(f"Processing mod file: {mod_path}")
        try:
            mod = Mod(mod_path)
            print(mod)
            for ref in mod.references:
                print(f"Reference: {ref}")
            for req in mod.requires:
                print(f"Requires: {req}")
        except FileNotFoundError as e:
            print(e)
        except Exception as e:
            print(f"An error occurred: {e}")