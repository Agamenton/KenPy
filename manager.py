from pathlib import Path
import platform

from steam_library import get_workshop_of, KENSHI_WORKSHOP_ID
from mod import Mod, BASE_MODS


def topological_sort(graph: dict[str, list[str]]) -> list[str]:
    result = []
    visited = set()
    missing_items = []

    def visit(node):
        if node in visited:
            return
        visited.add(node)

        x = graph.get(node, [])
        if not x:
            if node not in graph:
                missing_items.append(node)
        else:
            for neighbor in x:
                visit(neighbor)
        result.append(node)

    for node in graph.keys():
        visit(node)

    return result, missing_items


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
        if not item.is_dir():
            if item.match(pattern) and (item.name not in [path.name for path in matches]):
                matches.append(item)
        else:
            if level:
                new_matches = find_files(item, pattern, level - 1)
                for match in new_matches:
                    if match.match(pattern) and (match.name not in [path.name for path in matches]):
                        matches.append(match)
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
                
        self.all_mods = self.find_all_mods()

        self.active_mods: list[Mod] = []
        for mod_name in active_mod_names:
            mod = next((m for m in self.all_mods if m.path.name == mod_name), None)
            if mod:
                self.active_mods.append(mod)
        
        self.save_all_mods()    # Tell Kenshi about all mods, so it does not automaticall enable them

    def __str__(self):
        return f"Manager(kenshi_dir='{self.kenshi_dir}', all mods cnt='{len(self.all_mods)}', active mods cnt='{len(self.active_mods)}')"
    
    def __repr__(self):
        return f"Manager('{self.kenshi_dir}', {len(self.all_mods)}, {len(self.active_mods)})"
    
    def sorted_active_mods(self):
        """
        Topological sort of the active mods.
        It will try to keep the same order.
        If a mod has list of required mods, they will be placed before the mod itself.
        """
        def to_graph(mods):
            graph = {mod.path.name: [] for mod in mods}
            for mod in mods:
                graph[mod.path.name] = [req for req in mod.requires if req not in BASE_MODS]
            return graph
        
        graph = to_graph(self.active_mods)

        missing_mods = []
        sorted_mods, missing_mods = topological_sort(graph)
        sorted_active_mods = []
        for mod_name in sorted_mods:
            mod = next((m for m in self.active_mods if m.path.name == mod_name), None)
            if mod:
                sorted_active_mods.append(mod)
        return sorted_active_mods, missing_mods
    
    def sort_active_mods(self):
        """
        Sort the active mods in a topological order based on their dependencies.
        This will modify the active_mods list.
        """
        sorted_mods, missing_mods = self.sorted_active_mods()
        self.active_mods = sorted_mods
        return missing_mods

    def has_all_requirements(self, mod: Mod):
        """
        Check if all dependencies of a mod are in the active_mods list.
        :param mod: Mod instance to check.
        :return: True if all dependencies are satisfied, False otherwise.
        """
        if not isinstance(mod, Mod):
            raise ValueError("mod must be an instance of Mod.")
        
        all_mods = [m.path.name for m in self.active_mods]
        for dependency in mod.requires:
            if dependency not in all_mods:
                return False
        return True
    
    def is_in_correct_order(self, mod: Mod):
        """
        Check if a mod is in the correct order based on its dependencies.
        The mod must be in the active_mods.
        :param mod: Mod instance to check.
        :return: True if the mod is in the correct order, False otherwise.
        """
        if not isinstance(mod, Mod):
            raise ValueError("mod must be an instance of Mod.")
    
        if mod not in self.active_mods:
            raise ValueError("Mod must be in the active_mods list to check its order.")
        
        if not self.has_all_requirements(mod):
            return False
        
        all_mods = [m.path.name for m in self.active_mods]
        for dependency in mod.requires:
            # Check if the dependency appears before the mod in the active_mods list
            if all_mods.index(dependency) > all_mods.index(mod.path.name):
                return False
        return True
    
    def save_active_mods(self):
        """
        Save the active mods to the active_mods_file.
        """
        with open(self.active_mods_file, 'w') as f:
            f.write('\n'.join([m.path.name for m in self.active_mods]))
            f.write('\n')  # This is what the official manager does
    
    def save_all_mods(self):
        all_mods_file = self.kenshi_dir / "data" / "__mods.list"
        with open(all_mods_file, 'w') as f:
            f.write('\n'.join([m.path.stem for m in self.all_mods]))
            f.write('\n')

    def inactive_mods(self):
        """
        Get a list of inactive mods (mods that are not in the active_mods list).
        """
        return [mod for mod in self.all_mods if mod not in self.active_mods]
    
    def mod_by_name(self, name):
        """
        Get a mod by its name.
        :param name: The name of the mod (without .mod extension).
        :return: Mod instance or None if not found.
        """
        if not name.endswith(".mod"):
            name += ".mod"
        return next((m for m in self.all_mods if m.path.name == name), None)
    
    def toggle_mod(self, mod):
        """
        Toggle the active state of a mod.
        If the mod is active, it will be removed from the active_mods list.
        If it is inactive, it will be added to the active_mods list.
        """
        if isinstance(mod, str):
            if not mod.endswith(".mod"):
                mod += ".mod"
            mod = Path(mod)
        if isinstance(mod, Path):
            mod = next((m for m in self.all_mods if m.path.name == mod.name), None)
        if not mod or not isinstance(mod, Mod):
            raise ValueError("Mod must be a Mod instance or a valid mod name.")
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
            
    def get_mods_from_save(self, save_path):
        """
        Get a list of mods used in a save file.
        A save file might contain a mod that is currently not downloaded.
        :param save_path: Path to the save file.
        :return: A tuple [0]=list of Mod instances used in correct order; [1]=list of mod names not downloaded
        """
        save_path = Path(save_path)
        if not save_path.exists():
            raise FileNotFoundError(f"Save file not found: {save_path}")
        
        mods = []
        not_found = []
        with open(save_path, 'rb') as f:
            content = f.read()

            # TODO: implement proper decoder of save files
            # because the following algorithm is so unreliable
            start = "mods"
            expected_amount = 9999999
            realistic_amount = 2000 # I highly doubt there will be more than 2000 mods in a save file
            start_index = content.find(start.encode())
            while True:
                # there is many ".mods" before the actual mods list starts
                if content[start_index-1] == ord('.'):
                    start_index = content.find(start.encode(), start_index + 1)
                else:
                    # it is possible to find "mods" without a "." infront but it might be a false positive if the next 4bytes are huge number
                    expected_amount = int.from_bytes(content[start_index+len(start):start_index+len(start)+4], 'little')
                    if expected_amount < realistic_amount:
                        break

            start_index += len(start) + 4
            mod_names = []
            mod_types = []
            vanilla_type = 4294967295
            while len(mod_names) < expected_amount:
                next_name_len = int.from_bytes(content[start_index:start_index+4], 'little')
                start_index += 4
                mod_name = content[start_index:start_index+next_name_len].decode('utf-8', errors='ignore')
                mod_names.append(mod_name)
                start_index += next_name_len
                mod_type = int.from_bytes(content[start_index:start_index+4], 'little')
                mod_types.append(mod_type)
                start_index += 4
                # skip next 8 bytes, I think they might be used as part of length of the mod name?
                start_index += 8
                if mod_type != vanilla_type:
                    # if mod type is not vanilla, it is a mod
                    mod = next((m for m in self.all_mods if m.name == mod_name), None)
                    if mod:
                        mods.append(mod)
                    else:
                        not_found.append(mod_name)       
                
        return (mods, not_found)
    
    def find_all_mods(self):
        all_mods = []
        kenshi_mods_folder = Path(self.kenshi_dir) / "mods"
        kenshi_workshop_folder = get_workshop_of(KENSHI_WORKSHOP_ID)
        if kenshi_mods_folder.exists():
            all_mods.extend(find_files(kenshi_mods_folder, "*.mod", 1))
        if kenshi_workshop_folder:
            kenshi_workshop_folder = Path(kenshi_workshop_folder)
            if kenshi_workshop_folder.exists():
                all_mods.extend(find_files(kenshi_workshop_folder, "*.mod", 1))
        all_mods = [Mod(mod) for mod in all_mods if mod.is_file()]
        return all_mods
    
    def check_for_new_mods(self):
        """
        Return true if there are new mods in the mods folder that are not in the all_mods list.
        """
        current_mods = self.find_all_mods()
        if len(current_mods) != len(self.all_mods):
            return True
        current_mod_names = {mod.path.name for mod in current_mods}
        existing_mod_names = {mod.path.name for mod in self.all_mods}
        if current_mod_names != existing_mod_names:
            return True
        return False

if __name__ == "__main__":
    # Example usage
    kenshi_dir = r"E:\SteamLibrary\steamapps\common\Kenshi"
    manager = Manager(kenshi_dir)
    mods = manager.get_mods_from_save(r"E:\SteamLibrary\steamapps\common\Kenshi\save\final6\quick.save")
    for mod in mods[0]:
        print(mod.name)
    for mod_name in mods[1]:
        print(f"Mod not found: {mod_name}")
    print("**" * 20)
    manager.get_mods_from_save(r"E:\SteamLibrary\steamapps\common\Kenshi\save\krals_chosen\quick.save")