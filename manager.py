from pathlib import Path
import platform

from steam_library import get_workshop_of, KENSHI_WORKSHOP_ID
from mod import Mod


def find_files(root, pattern, level=0):
    """
    Find files in a directory recursively matching a pattern.
    :param root: The root directory to start searching from.
    :param pattern: The file pattern to match (e.g., '*.mod').
    :param level: The current recursion level (0 = check only root then stop recursion).
    :return: A list of matching file paths.
    """
    root = Path(root)
    matches = []
    for item in root.iterdir():
        if item.is_dir():
            if level:
                matches.extend(find_files(item, pattern, level - 1))
        elif item.match(pattern):
            matches.append(item)
    return matches


class Manager:
    """
    Mod manager for Kenshi.
    """
    def __init__(self, kenshi_dir):
        if not kenshi_dir:
            raise ValueError("Kenshi directory must be set.")
        self.kenshi_dir = Path(kenshi_dir)
        
        self.active_mods_file = Path(kenshi_dir) / "data" / "mods.cfg"

        active_mod_names = []
        if self.active_mods_file.exists():
            with open(self.active_mods_file, 'r') as f:
                active_mod_names = f.read().splitlines()
                
        self.all_mods = []
        kenshi_mods_folder = Path(kenshi_dir) / "mods"
        kenshi_workshop_folder = get_workshop_of(KENSHI_WORKSHOP_ID)
        if kenshi_mods_folder.exists():
            self.all_mods.extend(find_files(kenshi_mods_folder, "*.mod", 1))
        if kenshi_workshop_folder:
            kenshi_workshop_folder = Path(kenshi_workshop_folder)
            if kenshi_workshop_folder.exists():
                self.all_mods.extend(find_files(kenshi_workshop_folder, "*.mod", 1))
        self.all_mods = [Mod(mod) for mod in self.all_mods if mod.is_file()]

        self.active_mods: list[Mod] = []
        for mod_name in active_mod_names:
            mod = next((m for m in self.all_mods if m.path.name == mod_name), None)
            if mod:
                self.active_mods.append(mod)

    def __str__(self):
        return f"Manager(kenshi_dir='{self.kenshi_dir}', all mods cnt='{len(self.all_mods)}', active mods cnt='{len(self.active_mods)}')"
    
    def __repr__(self):
        return f"Manager('{self.kenshi_dir}', {len(self.all_mods)}, {len(self.active_mods)})"
    
    def save_active_mods(self):
        """
        Save the active mods to the active_mods_file.
        """
        with open(self.active_mods_file, 'w') as f:
            f.write('\n'.join([m.path.name for m in self.active_mods]))
            f.write('\n')  # This is what the official manager does
    
    def inactive_mods(self):
        """
        Get a list of inactive mods (mods that are not in the active_mods list).
        """
        return [mod for mod in self.all_mods if mod not in self.active_mods]
    
    def toggle_mod(self, mod: Mod):
        """
        Toggle the active state of a mod.
        If the mod is active, it will be removed from the active_mods list.
        If it is inactive, it will be added to the active_mods list.
        """
        if mod in self.active_mods:
            self.active_mods.remove(mod)
        else:
            self.active_mods.append(mod)

    def saves_location(self):
        """
        Get the location of the saves folder.
        Checks settings.cfg to determine where the saves are stored.
        If the setting is not found, raises FileNotFoundError.
        If the saves are stored in users location and system is not Windows, raises NotImplementedError.
        """
        settings_file = self.kenshi_dir / "settings.cfg"
        if not settings_file.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_file}")
        is_user_location = 0
        with open(settings_file, 'r') as f:
            for line in f:
                if line.startswith("User save location="):
                    is_user_location = int(line.split('=')[1].strip())
                    break
        if not is_user_location:
            return self.kenshi_dir / "save"
        else:
            # appdata local kenshi save
            # TODO: make this cross-platform
            if platform.system() == "Windows":
                return Path.home() / "AppData" / "Local" / "Kenshi" / "save"
            else:
                raise NotImplementedError("User save location for non-Windows platforms is not implemented yet.")


if __name__ == "__main__":
    # Example usage
    kenshi_dir = r"E:\SteamLibrary\steamapps\common\Kenshi"
    manager = Manager(kenshi_dir)
    for mod in manager.all_mods:
        print(mod.name)
    print(len(manager.all_mods), "manager.all_mods found.")

    print("**" * 20)
    all_mods = find_files(Path(kenshi_dir) / "mods", "*.mod", 1)
    kenshi_workshop_dir = r"E:\SteamLibrary\steamapps\workshop\content\233860"
    all_mods += find_files(Path(kenshi_workshop_dir), "*.mod", 1)
    for mod in all_mods:
        print(mod.name)
    print(len(all_mods), "total mods found.")