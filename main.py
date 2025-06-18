import os
from pathlib import Path

from steam_library import get_steam_install_path, get_steam_library_folders, get_installed_steam_games
from config import Config

KENSHI_WORKSHOP_ID = "233860" # Steam Workshop ID for Kenshi
KENSHI_STEAM_NAME = "Kenshi"


def get_steam_kenshi_folder():
    """
    Find the Kenshi installation folder by checking common locations.
    """
    result = None

    steam_path = get_steam_install_path()
    
    if not steam_path:
        print("Steam installation path could not be determined.")
        return result
    
    library_folders = get_steam_library_folders(steam_path)
    
    if not library_folders:
        print("No Steam library folders found.")
        return result
    
    for library in library_folders:
        potential_path = os.path.join(library, "steamapps", "common", KENSHI_STEAM_NAME)
        if os.path.isdir(potential_path):
            result = potential_path
            break
    
    return result

def get_kenshi_folder_from_config():
    """
    Get the Kenshi installation folder from the configuration.
    If not set, return None.
    """
    config = Config()
    kenshi_dir = config.kenshi_dir
    if kenshi_dir and os.path.isdir(kenshi_dir):
        return kenshi_dir
    
    print("Kenshi directory not set in configuration or does not exist.")
    return None


def find_kenshi_folder():
    """
    Find the Kenshi installation folder by checking common locations.
    """
    kenshi_folder = get_kenshi_folder_from_config()
    if not kenshi_folder:
        kenshi_folder = get_steam_kenshi_folder()
    
    return kenshi_folder


def main():
    ...
    kenshi_folder = find_kenshi_folder()
    if not kenshi_folder:
        ...
        # TODO: display a dialog to let the user select the Kenshi installation folder
        #  and save it to the config
    # discover local mods
    # discover workshop mods
    # instantiate Mod objects
    # start GUI
    

if __name__ == "__main__":
    main()
