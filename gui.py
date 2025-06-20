from pathlib import Path
from tkinter import *
import time

from PIL import Image, ImageTk

from mod import Mod
from manager import Manager
from config import APP_NAME, Config
from steam_library import open_steam_with_url


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
    root.geometry("1200x600")
    root.minsize(800, 400)
    root.resizable(True, True)

    root.mainloop()

class Gui:
    def __init__(self, root: Tk, manager: Manager):
        self.root = root
        self.manager = manager
        
        # Track last click times for each listbox
        self.last_inactive_click = 0
        self.last_active_click = 0
        
        # Drag-and-drop variables
        self.drag_source = None
        self.drag_item_index = None
        self.drag_start_y = None
        
        # Main frame setup
        self.frame = Frame(self.root)
        self.frame.pack(fill=BOTH, expand=True)
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=2)  # Info frame
        self.frame.columnconfigure(1, weight=1)  # Inactive mods
        self.frame.columnconfigure(2, weight=1)  # Active mods
        self.frame.columnconfigure(3, weight=0)  # Buttons (fixed width)
        self.frame.rowconfigure(0, weight=1)     # Single row

        # Create frames
        self.info_frame = Frame(self.frame)
        self.info_frame.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        self.info_frame.columnconfigure(0, weight=1)
        self.info_frame.rowconfigure(0, weight=1)

        self.inactive_mods_frame = Frame(self.frame)
        self.inactive_mods_frame.grid(row=0, column=1, sticky=NSEW, padx=5, pady=5)
        self.inactive_mods_frame.columnconfigure(0, weight=1)
        self.inactive_mods_frame.rowconfigure(2, weight=1)

        self.active_mods_frame = Frame(self.frame)
        self.active_mods_frame.grid(row=0, column=2, sticky=NSEW, padx=5, pady=5)
        self.active_mods_frame.columnconfigure(0, weight=1)
        self.active_mods_frame.rowconfigure(2, weight=1)

        self.buttons_frame = Frame(self.frame)
        self.buttons_frame.grid(row=0, column=3, sticky=NS, padx=5, pady=5)

        self.create_widgets()

    def create_widgets(self):
        # -------------------
        # INACTIVE MODS FRAME
        self.inactive_count_frame = Frame(self.inactive_mods_frame)
        self.inactive_count_frame.grid(row=0, column=0, sticky=EW, padx=5, pady=5)
        self.inactive_count_label = Label(self.inactive_count_frame, text="Inactive Mods")
        self.inactive_count_label.pack(side=LEFT, padx=5, pady=5)
        self.inactive_count_value = Label(self.inactive_count_frame, text=str(len(self.manager.inactive_mods())))
        self.inactive_count_value.pack(side=RIGHT, padx=5, pady=5)

        self.search_bar = Entry(self.inactive_mods_frame)
        self.search_bar.grid(row=1, column=0, sticky=EW, padx=5, pady=5)
        self.search_bar.bind('<KeyRelease>', lambda e: self.populate_inactive_mods())

        self.inactive_mods_listbox = Listbox(self.inactive_mods_frame)
        self.inactive_mods_listbox.grid(row=2, column=0, sticky=NSEW, padx=5, pady=5)
        self.inactive_mods_listbox.bind('<<ListboxSelect>>', self.on_mod_select)
        self.inactive_mods_listbox.bind('<Button-1>', self.handle_inactive_click)
        self.inactive_mods_listbox.bind('<Button-3>', self.handle_mod_rightclick)

        # -------------------
        # ACTIVE MODS FRAME
        self.active_count_frame = Frame(self.active_mods_frame)
        self.active_count_frame.grid(row=0, column=0, sticky=EW, padx=5, pady=5)
        self.active_count_label = Label(self.active_count_frame, text="Active Mods")
        self.active_count_label.pack(side=LEFT, padx=5, pady=5)
        self.active_count_value = Label(self.active_count_frame, text=str(len(self.manager.active_mods)))
        self.active_count_value.pack(side=RIGHT, padx=5, pady=5)
        
        self.active_search_bar = Entry(self.active_mods_frame)
        self.active_search_bar.grid(row=1, column=0, sticky=EW, padx=5, pady=5)
        self.active_search_bar.bind('<KeyRelease>', lambda e: self.populate_active_mods())
        
        self.active_mods_listbox = Listbox(self.active_mods_frame)
        self.active_mods_listbox.grid(row=2, column=0, sticky=NSEW, padx=5, pady=5)
        self.active_mods_listbox.bind('<<ListboxSelect>>', self.on_mod_select)
        self.active_mods_listbox.bind('<Button-3>', self.handle_mod_rightclick)
        
        # Add drag-and-drop bindings for active mods list
        self.active_mods_listbox.bind('<ButtonPress-1>', self.drag_start)
        self.active_mods_listbox.bind('<B1-Motion>', self.drag_motion)
        self.active_mods_listbox.bind('<ButtonRelease-1>', self.drag_release)

        # Create the info text area
        self.info_text = Text(self.info_frame, wrap=WORD)
        self.info_text.grid(row=0, column=0, sticky=NSEW)
        
        scrollbar = Scrollbar(self.info_frame, command=self.info_text.yview)
        scrollbar.grid(row=0, column=1, sticky=NS)
        self.info_text.config(yscrollcommand=scrollbar.set)

        # Populate the listboxes
        self.update_mod_lists()

        # Create buttons
        self.clear_mods_button = Button(self.buttons_frame, text="Clear", command=self.clear_active_mods)
        self.clear_mods_button.pack(fill=X, padx=5, pady=5)
        self.reset_button = Button(self.buttons_frame, text="Reset", command=self.reset_modlist)
        self.reset_button.pack(fill=X, padx=5, pady=5)
        self.export_button = Button(self.buttons_frame, text="Export", command=self.export_modlist)
        self.export_button.pack(fill=X, padx=5, pady=5)
        self.import_button = Button(self.buttons_frame, text="Import", command=self.import_modlist)
        self.import_button.pack(fill=X, padx=5, pady=5)
        
        spacer = Frame(self.buttons_frame, height=0)
        spacer.pack(fill=Y, expand=True)
        
        self.save_button = Button(self.buttons_frame, text="Save", command=self.set_active_mods)
        self.save_button.pack(fill=X, padx=5, pady=5, side=BOTTOM)

    # ======================
    # DRAG AND DROP FUNCTIONALITY
    # ======================
    
    def drag_start(self, event):
        """Start a drag operation"""
        # Only allowed in the active mods list
        if event.widget != self.active_mods_listbox:
            return
        
        # also considered as click event
        self.handle_active_click(event)
            
        # Get the index of the item under the mouse
        index = event.widget.nearest(event.y)
        if index >= 0:
            self.drag_source = event.widget
            self.drag_item_index = index
            self.drag_start_y = event.y
            
            # Change cursor to indicate dragging
            event.widget.config(cursor="hand2")
    
    def drag_motion(self, event):
        """Handle drag motion events"""
        # Only process if we're in a drag operation
        if self.drag_source is None or self.drag_item_index is None:
            return
            
        # Calculate how far we've dragged
        delta_y = event.y - self.drag_start_y
        
        # Only move the item if we've moved at least 5 pixels
        if abs(delta_y) > 5:
            # Find the item we're hovering over
            target_index = event.widget.nearest(event.y)
            
            # Only move if we're dragging to a different position
            if target_index >= 0 and target_index != self.drag_item_index:
                # Move the mod in the manager's list
                mod = self.manager.active_mods.pop(self.drag_item_index)
                self.manager.active_mods.insert(target_index, mod)
                
                # Update the list display
                self.populate_active_mods()
                
                # Select the moved item
                event.widget.selection_clear(0, END)
                event.widget.selection_set(target_index)
                event.widget.activate(target_index)
                
                # Update our drag index to the new position
                self.drag_item_index = target_index
                
                # Update the start position for smooth dragging
                self.drag_start_y = event.y
    
    def drag_release(self, event):
        """End a drag operation"""
        # Reset drag state
        self.drag_source = None
        self.drag_item_index = None
        self.drag_start_y = None
        
        # Reset cursor to default
        event.widget.config(cursor="")
    
    # ======================
    # MOD LIST MANAGEMENT
    # ======================
    
    def handle_inactive_click(self, event):
        """Handle clicks in the inactive mods listbox"""
        # Get the item at the click position
        index = self.inactive_mods_listbox.nearest(event.y)
        
        # If this is a double-click (within 300ms of last click)
        current_time = event.time
        if current_time - self.last_inactive_click < 300 and self.last_inactive_click > 0:
            # Process as double-click
            self.toggle_mod_at_index(self.inactive_mods_listbox, index, "inactive")
            self.last_inactive_click = 0  # Reset
        else:
            # Single click - just select the item
            self.last_inactive_click = current_time
            self.inactive_mods_listbox.selection_clear(0, END)
            self.inactive_mods_listbox.selection_set(index)
            self.inactive_mods_listbox.activate(index)
            
            # Schedule reset of click tracker
            self.root.after(300, lambda: setattr(self, 'last_inactive_click', 0))

    def handle_active_click(self, event):
        """Handle clicks in the active mods listbox"""
        # Get the item at the click position
        index = self.active_mods_listbox.nearest(event.y)
        
        # If this is a double-click (within 300ms of last click)
        current_time = event.time
        if current_time - self.last_active_click < 300 and self.last_active_click > 0:
            # Process as double-click
            self.toggle_mod_at_index(self.active_mods_listbox, index, "active")
            self.last_active_click = 0  # Reset
        else:
            # Single click - just select the item
            self.last_active_click = current_time
            self.active_mods_listbox.selection_clear(0, END)
            self.active_mods_listbox.selection_set(index)
            self.active_mods_listbox.activate(index)
            
            # Schedule reset of click tracker
            self.root.after(300, lambda: setattr(self, 'last_active_click', 0))

    def toggle_mod_at_index(self, listbox, index, list_type):
        """Toggle mod at the specified index in the specified list"""
        if list_type == "active":
            if 0 <= index < len(self.manager.active_mods):
                mod = self.manager.active_mods[index]
                self.manager.toggle_mod(mod)
                # Move focus to inactive list
                self.inactive_mods_listbox.focus_set()
        elif list_type == "inactive":
            if 0 <= index < len(self.manager.inactive_mods()):
                mod = self.manager.inactive_mods()[index]
                self.manager.toggle_mod(mod)
                # Move focus to active list
                self.active_mods_listbox.focus_set()
        
        self.update_mod_lists()

    def update_mod_lists(self):
        """Update both mod lists and preserve scroll positions"""
        # Save scroll positions
        inactive_scroll = self.inactive_mods_listbox.yview()
        active_scroll = self.active_mods_listbox.yview()
        
        # Update the lists
        self.populate_active_mods()
        self.populate_inactive_mods()
        
        # Restore scroll positions
        self.inactive_mods_listbox.yview_moveto(inactive_scroll[0])
        self.active_mods_listbox.yview_moveto(active_scroll[0])
        
        self.root.update_idletasks()
    
    def populate_active_mods(self):
        """Populate the active mods listbox"""
        self.active_mods_listbox.delete(0, END)
        search_term = self.active_search_bar.get().strip().lower()
        for mod in self.manager.active_mods:
            if search_term and search_term not in mod.name.lower():
                continue
            self.active_mods_listbox.insert(END, mod.name)
        self.active_count_value.config(text=str(len(self.manager.active_mods)))
    
    def populate_inactive_mods(self):
        """Populate the inactive mods listbox"""
        self.inactive_mods_listbox.delete(0, END)
        search_term = self.search_bar.get().strip().lower()
        for mod in self.manager.inactive_mods():
            if search_term and search_term not in mod.name.lower():
                continue
            self.inactive_mods_listbox.insert(END, mod.name)
        self.inactive_count_value.config(text=str(len(self.manager.inactive_mods())))
    
    # ======================
    # MOD INFORMATION DISPLAY
    # ======================
    
    def on_mod_select(self, event):
        """Handle mod selection events"""
        widget = event.widget
        if widget == self.active_mods_listbox:
            index = widget.curselection()
            if index:
                mod = self.manager.active_mods[index[0]]
                self.display_mod_info(mod)
        elif widget == self.inactive_mods_listbox:
            index = widget.curselection()
            if index:
                mod = self.manager.inactive_mods()[index[0]]
                self.display_mod_info(mod)
    
    def display_mod_info(self, mod: Mod):
        """Display information about the selected mod"""
        self.info_text.delete(1.0, END)
        self.info_text.insert(END, str(mod))

    def handle_mod_rightclick(self, event):
        """Handle right-click context menu for mods"""
        widget = event.widget
        index = widget.nearest(event.y)

        if isinstance(widget, Listbox):
            widget.selection_clear(0, END)
            widget.selection_set(index)
            widget.activate(index)
            modlist = self.manager.active_mods if widget == self.active_mods_listbox else self.manager.inactive_mods()
            self.display_mod_info(modlist[index])
        
        if index < 0:
            return
        
        # Create context menu
        context_menu = Menu(self.root, tearoff=0)
        # commands: open folder, open URL in browser, open URL in Steam, copy mod path to clipboard, copy URL to clipboard
        mod = None
        if widget == self.active_mods_listbox:
            mod = self.manager.active_mods[index]
        elif widget == self.inactive_mods_listbox:
            mod = self.manager.inactive_mods()[index]
        if mod:
            context_menu.add_command(label="Open Mod Folder", command=lambda: self.open_folder(mod))
            
            # DEV-NOTE: Gui class probably should not be responsible for this
            if mod.web_url:
                context_menu.add_command(label="Open URL in Browser", command=lambda: self.open_url(mod))
            if mod.steam_url:
                context_menu.add_command(label="Open URL in Steam", command=lambda: self.open_steam_url(mod))
            context_menu.add_command(label="Copy Mod Path", command=lambda: self.copy_mod_path(mod))
            if mod.web_url:
                context_menu.add_command(label="Copy URL", command=lambda: self.copy_url(mod))
        
        # Show the context menu
        context_menu.post(event.x_root, event.y_root)
    
    def open_folder(self, mod: Mod):
        """Open the mod's folder in the file explorer"""
        import os
        os.startfile(mod.path.parent)

    def open_url(self, mod: Mod):
        """Open the mod's URL in the default web browser"""
        import webbrowser
        url = mod.web_url
        if url:
            webbrowser.open(url)

    def open_steam_url(self, mod: Mod):
        """Open the mod's URL in the Steam client"""
        url = mod.steam_url
        if url:
            open_steam_with_url(url)

    def copy_mod_path(self, mod: Mod):
        """Copy the mod's path to the clipboard"""
        # TODO:

    def copy_url(self, mod: Mod):
        """Copy the mod's URL to the clipboard"""
        # TODO
        
    # ======================
    # MOD LIST OPERATIONS
    # ======================
    
    def export_modlist(self):
        """Export the current active mods to a text file"""
        modlist_data = "\n".join(mod.path.name for mod in self.manager.active_mods)
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
        """Import a mod list from a text file"""
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
        """Save the current active mods"""
        self.manager.save_active_mods()

    def clear_active_mods(self):
        """Clear the active mods list"""
        self.manager.active_mods.clear()
        self.update_mod_lists()
        self.info_text.delete(1.0, END)

    def reset_modlist(self):
        """Reset the mod manager to its initial state"""
        self.manager = Manager(self.manager.kenshi_dir)
        self.update_mod_lists()
        self.info_text.delete(1.0, END)