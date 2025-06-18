import os
import platform
import vdf


class SteamGame:
    def __init__(self, appid, name, install_dir):
        self.appid = appid
        self.name = name
        self.install_dir = install_dir

    def __str__(self):
        return f"SteamGame(appid={self.appid}, name='{self.name}', install_dir='{self.install_dir}')"
    
    def __repr__(self):
        return f"SteamGame({self.appid}, '{self.name}', '{self.install_dir}')"


def get_steam_install_path():
    os_type = platform.system()

    if os_type == "Windows":
        try:
            import winreg
            # Try 64-bit registry first
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            except FileNotFoundError:
                # Fallback to 32-bit registry
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam")
            
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            winreg.CloseKey(key)
            return path
        except ImportError:
            print("winreg not found. This script requires it on Windows.")
            return None
        except FileNotFoundError:
            print("Steam registry key not found. Is Steam installed?")
            return None
    elif os_type == "Linux":
        # Common Linux paths
        linux_paths = [
            os.path.expanduser("~/.local/share/Steam"),
            os.path.expanduser("~/.steam/steam"),
            "/usr/share/steam", # For system-wide installations (less common for user games)
        ]
        for path in linux_paths:
            if os.path.isdir(path):
                # Ensure we return the root Steam directory, not just steamapps
                # Some Linux paths directly point to the Steam client root
                if os.path.basename(path).lower() == "steam":
                    return path
                elif os.path.basename(path).lower() == "steamapps" and os.path.isdir(os.path.join(os.path.dirname(path), 'bin')):
                    # If it's steamapps, go up one level to the root Steam folder
                    return os.path.dirname(path)
        print("Steam installation not found in common Linux paths.")
        return None
    elif os_type == "Darwin":  # macOS
        # Common macOS path
        mac_path = os.path.expanduser("~/Library/Application Support/Steam")
        if os.path.isdir(mac_path):
            return mac_path
        print("Steam installation not found in common macOS path.")
        return None
    else:
        print(f"Unsupported operating system: {os_type}")
        return None


def get_steam_library_folders(steam_install_path):
    if not steam_install_path:
        return []

    library_folders_path = os.path.join(steam_install_path, "steamapps", "libraryfolders.vdf")
    
    # Initialize with the default library path
    library_paths = [os.path.join(steam_install_path, "steamapps")]

    if not os.path.exists(library_folders_path):
        print(f"libraryfolders.vdf not found at: {library_folders_path}. Only checking default SteamApps.")
        # Even if libraryfolders.vdf is missing, the primary steamapps folder should still be checked
        return library_paths

    try:
        with open(library_folders_path, 'r', encoding='utf-8') as f:
            library_data = vdf.load(f)

        if 'libraryfolders' in library_data:
            for key, value in library_data['libraryfolders'].items():
                if key.isdigit() and 'path' in value:
                    # The 'path' in libraryfolders.vdf directly points to the root of the library (e.g., D:\SteamLibrary)
                    # We need to append 'steamapps' to it to get to the appmanifests and common folders
                    full_library_path = os.path.join(value['path'], "steamapps")
                    if os.path.isdir(full_library_path) and full_library_path not in library_paths:
                        library_paths.append(full_library_path)
        return library_paths
    except Exception as e:
        print(f"Error reading libraryfolders.vdf: {e}")
        return library_paths


def get_installed_steam_games(library_paths):
    installed_games = []
    for steamapps_folder in library_paths: # Now library_paths contains the full 'steamapps' paths
        common_path = os.path.join(steamapps_folder, "common")

        if not os.path.isdir(steamapps_folder):
            print(f"Warning: SteamApps folder not found at {steamapps_folder}. Skipping.")
            continue
        if not os.path.isdir(common_path):
            print(f"Warning: 'common' folder not found within {steamapps_folder}. Skipping.")
            continue


        for filename in os.listdir(steamapps_folder):
            if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                filepath = os.path.join(steamapps_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        game_data = vdf.load(f)
                    
                    app_state = game_data.get("AppState", {})
                    appid = app_state.get("appid")
                    name = app_state.get("name")
                    install_dir_relative = app_state.get("installdir")

                    if appid and name and install_dir_relative:
                        # Construct the full game path using the 'common' folder for this specific library
                        game_folder = os.path.join(common_path, install_dir_relative)
                        
                        if os.path.isdir(game_folder):
                            installed_games.append(SteamGame(appid, name, game_folder))
                        else:
                            print(f"Warning: Game folder '{game_folder}' for '{name}' (AppID: {appid}) does not exist. Manifest might be outdated or game moved.")
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")
    return installed_games


if __name__ == "__main__":
    steam_path = get_steam_install_path()

    if steam_path:
        print(f"Steam installation found at: {steam_path}")
        library_folders = get_steam_library_folders(steam_path)

        if library_folders:
            print("\nSteam Library 'steamapps' Folders (where manifest files are located):")
            for folder in library_folders:
                print(f"- {folder}")

            installed_games = get_installed_steam_games(library_folders)

            if installed_games:
                print("\nInstalled Steam Games:")
                for game in installed_games:
                    print(f"- {game.name} (AppID: {game.appid}) - Installed at: {game.install_dir}")
            else:
                print("\nNo installed Steam games found across all libraries.")
        else:
            print("\nCould not find any Steam library 'steamapps' folders.")
    else:
        print("\nCould not locate Steam installation.")