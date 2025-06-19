from pathlib import Path
from tkinter import *

from PIL import Image, ImageTk

from mod import Mod
from manager import Manager
from config import APP_NAME, Config

def start_gui(manager: Manager):
    """
    Start the GUI for the mod manager.
    """
    root = Tk()
    root.title(APP_NAME)
    
    # Load and set the icon
    icon_path = Path(__file__).parent / "assets" / "icon.png"
    if icon_path.exists():
        icon_image = Image.open(icon_path)
        icon_photo = ImageTk.PhotoImage(icon_image)
        root.iconphoto(False, icon_photo)
    
    gui = Gui(root, manager)
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.geometry("800x600")
    root.resizable(True, True)

    root.mainloop()

class Gui:
    def __init__(self, root: Tk, manager: Manager):
        self.root = root
        self.manager = manager

        self.frame = Frame(self.root)
        self.frame.pack(fill=BOTH, expand=True)

        self.info_frame = Frame(self.frame)
        self.info_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.inactive_mods_frame = Frame(self.frame)
        self.inactive_mods_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.active_mods_frame = Frame(self.frame)
        self.active_mods_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.buttons_frame = Frame(self.frame)
        self.buttons_frame.pack(side=RIGHT, fill=Y)

        self.create_widgets()

    def create_widgets(self):
        # -------------------
        # INACTIVE MODS FRAME
        self.inactive_count_frame = Frame(self.inactive_mods_frame)
        self.inactive_count_frame.pack(fill=X, padx=5, pady=5)
        self.inactive_count_label = Label(self.inactive_count_frame, text="Inactive Mods")
        self.inactive_count_label.pack(side=LEFT, padx=5, pady=5)
        self.inactive_count_value = Label(self.inactive_count_frame, text=str(len(self.manager.inactive_mods())))
        self.inactive_count_value.pack(side=RIGHT, padx=5, pady=5)

        # Search bar for inactive mods
        self.search_bar = Entry(self.inactive_mods_frame)
        self.search_bar.pack(fill=X, padx=5, pady=5)
        self.search_bar.bind('<KeyRelease>', lambda e: self.populate_inactive_mods())

        # Create the listbox for inactive mods
        self.inactive_mods_listbox = Listbox(self.inactive_mods_frame, selectmode=SINGLE)
        self.inactive_mods_listbox.pack(fill=BOTH, expand=True)
        self.inactive_mods_listbox.bind('<<ListboxSelect>>', self.on_mod_select)
        self.inactive_mods_listbox.bind('<Double-Button-1>', lambda e: self.toggle_mod())

        # -------------------
        # ACTIVE MODS FRAME
        self.active_count_frame = Frame(self.active_mods_frame)
        self.active_count_frame.pack(fill=X, padx=5, pady=5)
        self.active_count_label = Label(self.active_count_frame, text="Active Mods")
        self.active_count_label.pack(side=LEFT, padx=5, pady=5)
        self.active_count_value = Label(self.active_count_frame, text=str(len(self.manager.active_mods)))
        self.active_count_value.pack(side=RIGHT, padx=5, pady=5)
        # Search bar for active mods
        self.active_search_bar = Entry(self.active_mods_frame)
        self.active_search_bar.pack(fill=X, padx=5, pady=5)
        self.active_search_bar.bind('<KeyRelease>', lambda e: self.populate_active_mods())
        # Create the listbox for active mods
        self.active_mods_listbox = Listbox(self.active_mods_frame, selectmode=SINGLE)
        self.active_mods_listbox.pack(fill=BOTH, expand=True)
        self.active_mods_listbox.bind('<<ListboxSelect>>', self.on_mod_select)
        self.active_mods_listbox.bind('<Double-Button-1>', lambda e: self.toggle_mod())

        # Create the info text area
        self.info_text = Text(self.info_frame, wrap=WORD)
        self.info_text.pack(fill=BOTH, expand=True)

        # Populate the listboxes
        self.update_mod_lists()

        # Create buttons: reset, export, import, save
        self.clear_mods_button = Button(self.buttons_frame, text="Clear", command=self.clear_active_mods)
        self.clear_mods_button.pack(fill=X, padx=5, pady=5)
        self.reset_button = Button(self.buttons_frame, text="Reset", command=self.reset_modlist)
        self.reset_button.pack(fill=X, padx=5, pady=5)
        self.export_button = Button(self.buttons_frame, text="Export", command=self.export_modlist)
        self.export_button.pack(fill=X, padx=5, pady=5)
        self.import_button = Button(self.buttons_frame, text="Import", command=self.import_modlist)
        self.import_button.pack(fill=X, padx=5, pady=5)
        self.save_button = Button(self.buttons_frame, text="Save", command=self.set_active_mods)
        self.save_button.pack(fill=X, padx=5, pady=5, side=BOTTOM)

    def export_modlist(self):
        """
        Export the current active mods to a text file.
        """        
        modlist_data = "\n".join(mod.path.name for mod in self.manager.active_mods)
        # ask user for a file name via a file dialog
        from tkinter import filedialog
        default_dir = Path(Config.get_config_dir(APP_NAME)) / "modlists"
        default_dir.mkdir(parents=True, exist_ok=True)
        file_path = filedialog.asksaveasfilename(
            title="Save Mod List",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=default_dir,
            initialfile=""
        )
        if file_path:
            with open(file_path, 'w') as f:
                f.write(modlist_data)

    def import_modlist(self):
        """
        Import a mod list from a text file.
        This should be called when the user clicks the import button.
        """
        from tkinter import filedialog
        default_dir = Path(Config.get_config_dir(APP_NAME)) / "modlists"
        if not default_dir.exists():
            default_dir = Path(__file__).parent
        file_path = filedialog.askopenfilename(
            title="Open Mod List",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=default_dir
        )
        if file_path:
            with open(file_path, 'r') as f:
                mod_names = f.read().splitlines()
                self.manager.active_mods.clear()
                for mod_name in mod_names:
                    mod = next((m for m in self.manager.all_mods if m.path.name == mod_name), None)
                    if mod:
                        self.manager.active_mods.append(mod)
            self.update_mod_lists()

    def set_active_mods(self):
        """
        Save the current active mods to the active_mods_file.
        This should be called when the user clicks the save button.
        """
        self.manager.save_active_mods()

    def clear_active_mods(self):
        """
        Clear the active mods list and update the GUI.
        This should be called when the user clicks the Clear button.
        """
        self.manager.active_mods.clear()
        self.update_mod_lists()
        self.info_text.delete(1.0, END)

    def reset_modlist(self):
        """
        Reset the mod manager to its initial state (or to last Save).
        This should be called when the user clicks the Reset button.
        """
        self.manager = Manager(self.manager.kenshi_dir)
        self.update_mod_lists()
        self.info_text.delete(1.0, END)

    def update_mod_lists(self):
        """
        Update the active and inactive mods lists.
        This should be called after any changes to the mod list.
        """
        self.populate_active_mods()
        self.populate_inactive_mods()

    def populate_active_mods(self):
        """
        Populate the active mods listbox with the names of active mods.
        """
        self.active_mods_listbox.delete(0, END)
        search_term = self.active_search_bar.get().strip().lower()
        for mod in self.manager.active_mods:
            if search_term and search_term not in mod.name.lower():
                continue
            self.active_mods_listbox.insert(END, mod.name)
        self.active_count_value.config(text=str(len(self.manager.active_mods)))

    def populate_inactive_mods(self):
        """
        Populate the inactive mods listbox with the names of inactive mods.
        """
        self.inactive_mods_listbox.delete(0, END)

        search_term = self.search_bar.get().strip().lower()

        for mod in self.manager.inactive_mods():
            if search_term and search_term not in mod.name.lower():
                continue
            self.inactive_mods_listbox.insert(END, mod.name)
        self.inactive_count_value.config(text=str(len(self.manager.inactive_mods())))
    
    def on_mod_select(self, event):
        selected_index = self.active_mods_listbox.curselection()
        if selected_index:
            mod = self.manager.active_mods[selected_index[0]]
            self.display_mod_info(mod)
        else:
            selected_index = self.inactive_mods_listbox.curselection()
            if selected_index:
                mod = self.manager.inactive_mods()[selected_index[0]]
                self.display_mod_info(mod)

    def display_mod_info(self, mod: Mod):
        """
        Display the information of the selected mod in the info text area.
        """
        self.info_text.delete(1.0, END)
        self.info_text.insert(END, str(mod))

    def toggle_mod(self):
        """
        Toggle the selected mod between active and inactive.
        """
        selected_index = self.active_mods_listbox.curselection()
        if selected_index:
            mod = self.manager.active_mods[selected_index[0]]
            self.manager.toggle_mod(mod)
            self.update_mod_lists()
            self.display_mod_info(mod)
        else:
            selected_index = self.inactive_mods_listbox.curselection()
            if selected_index:
                mod = self.manager.inactive_mods()[selected_index[0]]
                self.manager.toggle_mod(mod)
                self.update_mod_lists()
                self.display_mod_info(mod)
