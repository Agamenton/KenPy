from pathlib import Path

from steam_library import get_workshop_of, KENSHI_WORKSHOP_ID
from mod import Mod


class Manager:
    """
    Mod manager for Kenshi.
    """
    def __init__(self, kenshi_dir):
        if not kenshi_dir:
            raise ValueError("Kenshi directory must be set.")
        self.kenshi_dir = Path(kenshi_dir)
        
        self.active_mods_file = Path(kenshi_dir) / "data" / "mods.cfg"

        self.active_mods = []
        if self.active_mods_file.exists():
            with open(self.active_mods_file, 'r') as f:
                self.active_mods = f.read().splitlines()
                
        self.all_mods = []
        kenshi_mods_folder = Path(kenshi_dir) / "mods"
        kenshi_workshop_folder = get_workshop_of(KENSHI_WORKSHOP_ID)
        if kenshi_mods_folder.exists():
            self.all_mods.extend(kenshi_mods_folder.rglob("*.mod"))
        if kenshi_workshop_folder:
            kenshi_workshop_folder = Path(kenshi_workshop_folder)
            if kenshi_workshop_folder.exists():
                self.all_mods.extend(kenshi_workshop_folder.rglob("*.mod"))
        self.all_mods = [Mod(mod) for mod in self.all_mods if mod.is_file()]

    def __str__(self):
        return f"Manager(kenshi_dir='{self.kenshi_dir}', all mods cnt='{len(self.all_mods)}', active mods cnt='{len(self.active_mods)}')"
    
    def __repr__(self):
        return f"Manager('{self.kenshi_dir}', {len(self.all_mods)}, {len(self.active_mods)})"


if __name__ == "__main__":
    # Example usage
    kenshi_dir = r"E:\SteamLibrary\steamapps\common\Kenshi"  # Replace with actual Kenshi directory
    manager = Manager(kenshi_dir)
    print(manager)
    for mod in manager.all_mods:
        print(mod)