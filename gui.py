from pathlib import Path
from tkinter import *
from tkinter import messagebox, filedialog
from tkinter import ttk
import time
import os
import subprocess

from PIL import Image, ImageTk

from mod import Mod
from manager import Manager, ModlistDiff
from config import APP_NAME, Config, APP_TITLE
from steam_library import open_steam_with_url, get_workshop_of, KENSHI_WORKSHOP_ID


# primary palette colors
COLOR_DARK_PRIMARY = "#3E3E3E"
COLOR_DARK_SECONDARY = "#FFFCD6"

COLOR_LIGHT_PRIMARY = "#FFFFFF"
COLOR_LIGHT_SECONDARY = "#000000"

COLOR_LIGHT_SCROLLBAR_TR = "#B8B8B8"

COLOR_ERROR = "#FF0000"  # red for errors
COLOR_WARNING = "#FFA500"  # orange for warnings

# background color of mods in listboxes when selected
COLOR_SELECT_DARK = "#273166"
COLOR_SELECT_LIGHT = "#5B71E1"

# text color when mouse hover over mods
COLOR_HOVER_DARK = "#5f5de6"
COLOR_HOVER_LIGHT = "#0400ff"

# button colors
COLOR_SAVE_BTN_BG_READY = "#427374"
COLOR_RELOAD_BTN_BG_READY = COLOR_SAVE_BTN_BG_READY # for consistency


def select_kenshi_folder():
    """
    Prompt the user to select the Kenshi installation folder.
    """
    root = Tk()
    root.withdraw()  # Hide the root window
    folder = filedialog.askdirectory(
        title="Select Kenshi Installation Folder",
        initialdir=os.path.expanduser("~"),
        mustexist=True
    )
    if folder:
        return Path(folder)
    return None


def start_gui(manager: Manager):
    """
    Start the GUI for the mod manager.
    """
    root = Tk()
    root.title(APP_TITLE)
    
    # Load and set the icon
    icon_path = Path(__file__).parent / "icon.ico"
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

        self.needs_save = False

        self.needs_reload = False
        
        # Track last click times for each listbox
        self.last_inactive_click = 0
        self.last_active_click = 0
        
        # Drag-and-drop variables
        self.drag_source = None
        self.drag_item = None
        self.drag_start_y = None
        
        # Main frame setup
        self.frame = Frame(self.root)
        self.frame.pack(fill=BOTH, expand=True)
        
        # Configure grid weights
        self.frame.columnconfigure(0, weight=2)  # Info frame
        self.frame.columnconfigure(1, weight=1)  # Inactive mods
        self.frame.columnconfigure(2, weight=1)  # Active mods
        self.frame.columnconfigure(3, weight=0)  # Buttons (fixed width)
        self.frame.rowconfigure(0, weight=0)     # Top row (paths and lists)
        self.frame.rowconfigure(1, weight=1)     # Bottom row (info frame)

        # Create frames
        self.paths_frame = Frame(self.frame)
        self.paths_frame.grid(row=0, column=0, sticky=EW, padx=5, pady=5)
        self.paths_frame.columnconfigure(0, weight=0)
        self.paths_frame.columnconfigure(1, weight=1)

        self.info_frame_width = 620
        self.info_frame = Frame(self.frame, width=self.info_frame_width)
        self.info_frame.grid(row=1, column=0, sticky=NSEW, padx=5, pady=5)
        self.info_frame.columnconfigure(0, weight=1)
        self.info_frame.rowconfigure(0, weight=1)
        self.current_img = None

        self.inactive_mods_frame = Frame(self.frame)
        self.inactive_mods_frame.grid(row=0, column=1, sticky=NSEW, padx=5, pady=5, rowspan=2)
        self.inactive_mods_frame.columnconfigure(0, weight=1)
        self.inactive_mods_frame.rowconfigure(2, weight=1)
        self.last_selected_inactive_mod_idx = None
        self.current_inactive_selection = []

        self.active_mods_frame = Frame(self.frame)
        self.active_mods_frame.grid(row=0, column=2, sticky=NSEW, padx=5, pady=5, rowspan=2)
        self.active_mods_frame.columnconfigure(0, weight=1)
        self.active_mods_frame.rowconfigure(2, weight=1)
        self.last_selected_active_mod_idx = None
        self.current_active_selection = []

        self.ttk_style = ttk.Style(self.root)
        self.ttk_style.theme_use("clam")

        self.listbox_selected_item_bg = COLOR_SELECT_DARK

        self.buttons_frame = Frame(self.frame)
        self.buttons_frame.grid(row=0, column=3, sticky=NS, padx=5, pady=5, rowspan=2)

        self.create_widgets()

        self.periodic_check_for_mods()
        self.root.update()

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

        # Create container frame for listbox and scrollbar
        self.inactive_list_container = Frame(self.inactive_mods_frame)
        self.inactive_list_container.grid(row=2, column=0, sticky=NSEW, padx=5, pady=5)
        self.inactive_list_container.grid_rowconfigure(0, weight=1)
        self.inactive_list_container.grid_columnconfigure(0, weight=1)
        
        self.inactive_mods_listbox = Listbox(self.inactive_list_container, activestyle="none")
        self.inactive_mods_listbox.grid(row=0, column=0, sticky=NSEW)
        
        # Add scrollbar
        self.inactive_scrollbar = ttk.Scrollbar(self.inactive_list_container, command=self.inactive_mods_listbox.yview)
        self.inactive_scrollbar.grid(row=0, column=1, sticky=NS)
        self.inactive_mods_listbox.config(yscrollcommand=self.inactive_scrollbar.set)
        
        # Existing bindings
        self.inactive_mods_listbox.bind('<ButtonRelease-1>', self.handle_inactive_click)
        self.inactive_mods_listbox.bind('<Button-3>', self.handle_mod_rightclick)
        self.inactive_mods_listbox.bind('<Motion>', self.on_listbox_hover)
        self.inactive_mods_listbox.bind('<Leave>', self.on_listbox_leave)
        self.inactive_mods_listbox.bind('<KeyRelease>', self.on_keypress_listbox)
        self.inactive_mods_listbox.bind('<FocusOut>', lambda e: self.clear_inactive_selection())

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
        
        # Create container frame for listbox and scrollbar
        self.active_list_container = Frame(self.active_mods_frame)
        self.active_list_container.grid(row=2, column=0, sticky=NSEW, padx=5, pady=5)
        self.active_list_container.grid_rowconfigure(0, weight=1)
        self.active_list_container.grid_columnconfigure(0, weight=1)
        
        self.active_mods_listbox = Listbox(self.active_list_container, activestyle="none")
        self.active_mods_listbox.grid(row=0, column=0, sticky=NSEW)
        
        # Add scrollbar
        self.active_scrollbar = ttk.Scrollbar(self.active_list_container, command=self.active_mods_listbox.yview)
        self.active_scrollbar.grid(row=0, column=1, sticky=NS)
        self.active_mods_listbox.config(yscrollcommand=self.active_scrollbar.set)
        
        # Existing bindings
        self.active_mods_listbox.bind('<Button-3>', self.handle_mod_rightclick)
        self.active_mods_listbox.bind('<Motion>', self.on_listbox_hover)
        self.active_mods_listbox.bind('<Leave>', self.on_listbox_leave)
        self.active_mods_listbox.bind('<ButtonPress-1>', self.drag_start)
        self.active_mods_listbox.bind('<B1-Motion>', self.drag_motion)
        self.active_mods_listbox.bind('<ButtonRelease-1>', self.drag_release)
        self.active_mods_listbox.bind('<KeyRelease>', self.on_keypress_listbox)
        self.active_mods_listbox.bind('<FocusOut>', lambda e: self.clear_active_selection())

        # -------------------
        # PATHS FRAME
        self.btn_main_game_dir = Button(self.paths_frame, text="Game Dir", command=lambda: self.open_folder(self.manager.kenshi_dir))
        self.btn_main_game_dir.grid(row=0, column=0, sticky=W, padx=5, pady=5)
        self.btn_main_game_dir.config(width=15)

        self.lb_main_game_dir = Label(self.paths_frame, text=Path(self.manager.kenshi_dir).as_posix(), anchor=W, justify=LEFT)
        self.lb_main_game_dir.grid(row=0, column=1, sticky=EW, padx=5, pady=5,)
        self.lb_main_game_dir.bind("<Button-3>", self.kenshi_path_context_menu)

        self.btn_mods_dir = Button(self.paths_frame, text="Mods Dir", command=lambda: self.open_folder(self.manager.kenshi_dir / "mods"))
        self.btn_mods_dir.grid(row=1, column=0, sticky=EW, padx=5, pady=5)
        self.btn_mods_dir.config(width=15)

        self.lb_mods_dir = Label(self.paths_frame, text=Path(self.manager.kenshi_dir / "mods").as_posix(), anchor=W, justify=LEFT)
        self.lb_mods_dir.grid(row=1, column=1, sticky=EW, padx=5, pady=5)
        self.lb_mods_dir.bind("<Button-3>", lambda e: self.copy_context_menu(e, self.lb_mods_dir.cget("text")))

        workshop_dir = get_workshop_of(KENSHI_WORKSHOP_ID)
        if workshop_dir:
            workshop_dir = Path(workshop_dir).as_posix()
            self.btn_workshop_dir = Button(self.paths_frame, text="Workshop Dir", command=lambda: self.open_folder(workshop_dir))
        else:
            workshop_dir = "Not found"
            self.btn_workshop_dir = Button(self.paths_frame, text="Workshop Dir", state=DISABLED)
        self.btn_workshop_dir.grid(row=2, column=0, sticky=W, padx=5, pady=5)
        self.btn_workshop_dir.config(width=15)
        self.lb_workshop_dir = Label(self.paths_frame, text=workshop_dir, anchor=W, justify=LEFT)
        self.lb_workshop_dir.grid(row=2, column=1, sticky=EW, padx=5, pady=5)
        if workshop_dir != "Not found":
            self.lb_workshop_dir.bind("<Button-3>", lambda e: self.copy_context_menu(e, workshop_dir))

        # Populate the listboxes
        self.update_mod_lists()

        # -------------------
        # BUTTONS FRAME
        # Create buttons
        self.dark_mode = BooleanVar(value=Config().dark_mode)
        self.mode_checkbox = Checkbutton(self.buttons_frame, text="Dark Mode", variable=self.dark_mode, command=self.on_mode_change)
        self.mode_checkbox.pack(fill=X, padx=5, pady=5)

        self.clear_mods_button = Button(self.buttons_frame, text="Clear", command=self.clear_active_mods)
        self.clear_mods_button.pack(fill=X, padx=5, pady=5)
        self.reset_button = Button(self.buttons_frame, text="Reload", command=self.reset_modlist)
        self.reset_button.pack(fill=X, padx=5, pady=5)

        spacer = Frame(self.buttons_frame, height=0)
        spacer.pack(fill=Y, expand=True)

        self.export_button = Button(self.buttons_frame, text="Export list", command=self.export_modlist)
        self.export_button.pack(fill=X, padx=5, pady=5)
        self.import_button = Button(self.buttons_frame, text="Import list", command=self.import_modlist)
        self.import_button.pack(fill=X, padx=5, pady=5)
        self.import_save_button = Button(self.buttons_frame, text="Import save", command=self.import_modlist_from_save)
        self.import_save_button.pack(fill=X, padx=5, pady=5)
        
        spacer2 = Frame(self.buttons_frame, height=0)
        spacer2.pack(fill=Y, expand=True)

        self.sort_button = Button(self.buttons_frame, text="Sort", command=self.sort_active_mods)
        self.sort_button.pack(fill=X, padx=5, pady=5)

        spacer3 = Frame(self.buttons_frame, height=0)
        spacer3.pack(fill=Y, expand=True)
        
        self.launch_kenshi_button = Button(self.buttons_frame, text="Launch Kenshi", command=self.launch_kenshi)
        self.launch_kenshi_button.pack(fill=X, padx=5, pady=5, side=BOTTOM)

        self.save_button = Button(self.buttons_frame, text="Save", command=self.set_active_mods)
        self.save_button.pack(fill=X, padx=5, pady=5, side=BOTTOM)

        self.on_mode_change()
    
    def copy_to_clipboard(self, text):
        """Copy text to the clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def on_mode_change(self):
        """Toggle dark mode and update the configuration"""
        Config().dark_mode = self.dark_mode.get()
        if self.dark_mode.get():
            self.root.tk_setPalette(background=COLOR_DARK_PRIMARY, foreground=COLOR_DARK_SECONDARY)
            self.root.config(bg=COLOR_DARK_PRIMARY)
            self.mode_checkbox.config(fg=COLOR_DARK_SECONDARY, bg=COLOR_DARK_PRIMARY, selectcolor=COLOR_DARK_PRIMARY)
            self.listbox_selected_item_bg = COLOR_SELECT_DARK
            self.ttk_style.configure(
                'TScrollbar', 
                background=COLOR_DARK_SECONDARY, 
                troughcolor=COLOR_DARK_PRIMARY,
                arrowcolor=COLOR_DARK_PRIMARY,
                relief="groove"
            )
        else:
            self.root.tk_setPalette(background=COLOR_LIGHT_PRIMARY, foreground=COLOR_LIGHT_SECONDARY)
            self.root.config(bg=COLOR_LIGHT_PRIMARY)
            self.mode_checkbox.config(fg=COLOR_LIGHT_SECONDARY, bg=COLOR_LIGHT_PRIMARY, selectcolor=COLOR_LIGHT_PRIMARY)
            self.listbox_selected_item_bg = COLOR_SELECT_LIGHT
            self.ttk_style.configure(
                'TScrollbar',
                background=COLOR_LIGHT_PRIMARY,
                troughcolor=COLOR_LIGHT_SCROLLBAR_TR,
                arrowcolor=COLOR_LIGHT_SCROLLBAR_TR,
                relief='raised'
            )
            
        self.active_mods_listbox.config(
            selectbackground=self.listbox_selected_item_bg
        )
        self.active_scrollbar.config(style='TScrollbar')

        self.inactive_mods_listbox.config(
            selectbackground=self.listbox_selected_item_bg
        )
        self.inactive_scrollbar.config(style='TScrollbar')
        
        # Update info frame background
        self.info_frame.config(bg=self.root.cget('bg'))
        self.root.update_idletasks()
    

    # ======================
    # DRAG AND DROP FUNCTIONALITY
    # ======================
    
    def drag_start(self, event):
        """Start a drag operation"""
        # Only allowed in the active mods list
        if event.widget != self.active_mods_listbox:
            return
            
        # Get the index of the item under the mouse
        index = event.widget.nearest(event.y)
        if index >= 0:
            mod_name = event.widget.get(index)
            mod = self.manager.mod_by_name(mod_name)
            self.drag_source = event.widget
            self.drag_item = mod
            self.drag_item_index = index
            self.drag_start_y = event.y
            
            # Change cursor to indicate dragging
            event.widget.config(cursor="hand2")
    
    def drag_motion(self, event):
        """Handle drag motion events"""
        # Only process if we're in a drag operation
        if self.drag_source is None or self.drag_item is None:
            return
            
        # Calculate how far we've dragged
        delta_y = event.y - self.drag_start_y
        
        # Only move the item if we've moved at least 5 pixels
        if abs(delta_y) > 3:
            # Find the item we're hovering over
            target_index = event.widget.nearest(event.y)
            
            # Only move if we're dragging to a different position
            if target_index >= 0 and target_index != self.drag_item_index:
                # Move the mod in the manager's list
                target_mod_name = event.widget.get(target_index)
                target_mod = self.manager.mod_by_name(target_mod_name)
                target_manager_index = self.manager.active_mods.index(target_mod)
                self.manager.active_mods.remove(self.drag_item)
                self.manager.active_mods.insert(target_manager_index, self.drag_item)
                self.start_blinking()
                
                # Update the list display
                self.update_listbox_without_reset(self.active_mods_listbox)
                
                # Select the moved item
                event.widget.selection_clear(0, END)
                event.widget.selection_set(target_index)
                event.widget.activate(target_index)
                
                # Update our drag index to the new position
                mod_name = event.widget.get(target_index)
                mod = self.manager.mod_by_name(mod_name)
                self.drag_item = mod
                
                # Update the start position for smooth dragging
                self.drag_start_y = event.y
    
    def drag_release(self, event):
        """End a drag operation"""
        # Reset drag state
        self.drag_source = None
        self.drag_item = None
        self.drag_item_index = None
        self.drag_start_y = None
        
        # also considered as click event
        self.handle_active_click(event)
        
        # Reset cursor to default
        event.widget.config(cursor="")
    
    # ======================
    # MOD LIST MANAGEMENT
    # ======================

    def reset_last_active_mod_idx(self):
        """Clear selections in both listboxes"""
        self.last_selected_inactive_mod_idx = None
        self.last_selected_active_mod_idx = None
    
    def clear_active_selection(self):
        """Clear the current active selection"""
        self.current_active_selection = []
        self.update_mod_colors(self.active_mods_listbox, self.current_active_selection)

    def clear_inactive_selection(self):
        """Clear the current inactive selection"""
        self.current_inactive_selection = []
        self.update_mod_colors(self.inactive_mods_listbox, self.current_inactive_selection)

    def on_listbox_leave(self, event):
        """Reset the background color of all items in the listbox when mouse leaves"""
        widget = event.widget
        list_length = widget.size()
        for i in range(list_length):
            widget.itemconfig(i, {'fg': widget.cget('fg')})

    def on_listbox_hover(self, event):
        """Highlight the item under the mouse cursor in the listbox"""
        widget = event.widget
        index = widget.nearest(event.y)
        
        # set every item to normal
        list_length = widget.size()
        for i in range(list_length):
            widget.itemconfig(i, {'fg': widget.cget('fg')})

        # highlight the item under the cursor
        highlight_color = COLOR_HOVER_DARK if Config().dark_mode else COLOR_HOVER_LIGHT
        if index >= 0:
            widget.itemconfig(index, {'fg': highlight_color})
    
    def handle_inactive_click(self, event):
        """Handle clicks in the inactive mods listbox"""
        # Get the nearest item at the click position
        prev = self.last_selected_inactive_mod_idx
        self.reset_last_active_mod_idx()

        if not self.was_click_on_item(event, self.inactive_mods_listbox):
            self.inactive_mods_listbox.selection_clear(0, END)
            self.last_inactive_click = 0
            return
        
        index = self.inactive_mods_listbox.nearest(event.y)
        mod_name = self.inactive_mods_listbox.get(index)
        
        # If this is a double-click (within 300ms of last click)
        current_time = event.time
        if current_time - self.last_inactive_click < 300 and self.last_inactive_click > 0 and index == prev:
            # Process as double-click
            self.toggle_mod(mod_name)
            self.last_inactive_click = 0  # Reset
        else:
            # Single click - just select the item
            self.last_inactive_click = current_time
            self.inactive_mods_listbox.selection_clear(0, END)
            self.inactive_mods_listbox.selection_set(index)
            self.inactive_mods_listbox.activate(index)
            self.on_mod_select(event)  # Display mod info on single click
            # if shift was held, select all mods between previous and current selection
            if event.state & 0x0001:  # Shift key is held
                if prev is not None and prev != index:
                    start = min(prev, index)
                    end = max(prev, index)
                    self.inactive_mods_listbox.selection_set(start, end)
                    self.current_inactive_selection.extend(list(range(start, end + 1)))
            elif event.state & 0x0004:  # Control key is held
                # If Control is held, add/remove the item in the selection
                if index in self.current_inactive_selection:
                    self.current_inactive_selection.remove(index)
                else:
                    self.current_inactive_selection.append(index)
                self.last_selected_inactive_mod_idx = index
            else:
                self.current_inactive_selection = [index]
                self.last_selected_inactive_mod_idx = index
            
                # Schedule reset of click tracker
                self.root.after(300, lambda: setattr(self, 'last_inactive_click', 0))
                
            # update background color of items
            self.update_mod_colors(self.inactive_mods_listbox, self.current_inactive_selection)

    def handle_active_click(self, event):
        """Handle clicks in the active mods listbox"""
        prev = self.last_selected_active_mod_idx
        self.reset_last_active_mod_idx()

        if not self.was_click_on_item(event, self.active_mods_listbox):
            self.active_mods_listbox.selection_clear(0, END)
            self.last_active_click = 0
            return
        
        index = self.active_mods_listbox.nearest(event.y)
        mod_name = self.active_mods_listbox.get(index)
        
        # If this is a double-click (within 300ms of last click)
        current_time = event.time
        if current_time - self.last_active_click < 300 and self.last_active_click > 0 and index == prev:
            # Process as double-click
            self.toggle_mod(mod_name)
            self.last_active_click = 0  # Reset
        else:
            # Single click - just select the item
            self.last_active_click = current_time
            self.active_mods_listbox.selection_clear(0, END)
            self.active_mods_listbox.selection_set(index)
            self.active_mods_listbox.activate(index)
            self.on_mod_select(event)  # Display mod info on single click
            if event.state & 0x0001:  # Shift key is held
                if prev is not None and prev != index:
                    start = min(prev, index)
                    end = max(prev, index)
                    self.active_mods_listbox.selection_set(start, end)
                    self.current_active_selection.extend(list(range(start, end + 1)))
            elif event.state & 0x0004:  # Control key is held
                # If Control is held, add/remove the item in the selection
                if index in self.current_active_selection:
                    self.current_active_selection.remove(index)
                else:
                    self.current_active_selection.append(index)
                self.last_selected_active_mod_idx = index
            else:
                self.current_active_selection = [index]
                self.last_selected_active_mod_idx = index
            
                # Schedule reset of click tracker
                self.root.after(300, lambda: setattr(self, 'last_active_click', 0))
            
            # update background color of items
            self.update_mod_colors(self.active_mods_listbox, self.current_active_selection)

    def update_mod_colors(self, listbox, selection):
        """Update the background color of items in the listbox based on their selection state"""
        for i in range(listbox.size()):
            if listbox.itemcget(i, 'bg') in (COLOR_WARNING, COLOR_ERROR):
                continue
            if i in selection:
                listbox.itemconfig(i, {'bg': self.listbox_selected_item_bg})
            else:
                listbox.itemconfig(i, {'bg': self.root.cget('bg')})

    def was_click_on_item(self, event, listbox):
        """Check if the click in a listbox was on an item"""
        index = listbox.nearest(event.y)
        if index < 0 or index >= listbox.size():
            return False
        
        bbox = listbox.bbox(index)
        if bbox is None:
            return False
        
        item_y_top = bbox[1]
        item_y_bot = bbox[1] + bbox[3]
        if item_y_top <= event.y <= item_y_bot:
            return True
        return False
    
    def toggle_mod(self, mod_name, update=True):
        self.manager.toggle_mod(mod_name)
        self.start_blinking()
        if update:
            self.update_mod_lists()
            self.reset_last_active_mod_idx()
            self.current_active_selection = []
            self.current_inactive_selection = []

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

    def update_listbox_without_reset(self, listbox):
        """
        Update the listbox without resetting the scroll position.
        This should be useful when dragging mods in active mods listbox, so it does not reset the scroll position.
        """
        selected = listbox.curselection()
        scroll_pos = listbox.yview()

        if listbox == self.active_mods_listbox:
            self.populate_active_mods()
        elif listbox == self.inactive_mods_listbox:
            self.populate_inactive_mods()

        if selected:
            listbox.selection_set(selected[0])
            listbox.activate(selected[0])
        listbox.yview_moveto(scroll_pos[0])
    
    def populate_active_mods(self):
        """Populate the active mods listbox"""
        self.active_mods_listbox.delete(0, END)
        search_term = self.active_search_bar.get().strip().lower()
        mods_with_missing_reqs = []
        mods_with_misordered_reqs = []
        i = 0
        for mod in self.manager.active_mods:
            if search_term and search_term not in mod.name.lower():
                continue
            self.active_mods_listbox.insert(END, mod.name)
            
            if not self.manager.has_all_requirements(mod):
                mods_with_missing_reqs.append(i)
            elif not self.manager.is_in_correct_order(mod):
                mods_with_misordered_reqs.append(i)
            i += 1
                
        self.active_count_value.config(text=str(len(self.manager.active_mods)))

        for index in mods_with_misordered_reqs:
            self.active_mods_listbox.itemconfig(index, {'bg': COLOR_WARNING})
        for index in mods_with_missing_reqs:
            self.active_mods_listbox.itemconfig(index, {'bg': COLOR_ERROR})
    
    def populate_inactive_mods(self):
        """Populate the inactive mods listbox"""
        self.inactive_mods_listbox.delete(0, END)
        search_term = self.search_bar.get().strip().lower()
        for mod in self.manager.inactive_mods():
            if search_term and search_term not in mod.name.lower():
                continue
            self.inactive_mods_listbox.insert(END, mod.name)
        self.inactive_count_value.config(text=str(len(self.manager.inactive_mods())))
    
    def on_keypress_listbox(self, event):
        """Handle keypress events in the listboxes"""
        widget = event.widget
        if event.keysym == 'Return':
            if widget == self.active_mods_listbox:
                selection = self.current_active_selection
                listbox = self.active_mods_listbox
            elif widget == self.inactive_mods_listbox:
                selection = self.current_inactive_selection
                listbox = self.inactive_mods_listbox
            for i in selection:
                mod_name = listbox.get(i)
                if mod_name:
                    self.toggle_mod(mod_name, update=False)
            self.update_mod_lists() # update modlists after all mods were moved over

        # arrow up and down select mods
        elif event.keysym in ('Up', 'Down'):
            self.on_mod_select(event)  # Display mod info on keypress

    # ======================
    # MOD INFORMATION DISPLAY
    # ======================
    
    def on_mod_select(self, event):
        """Handle mod selection events"""
        widget = event.widget

        if widget == self.active_mods_listbox or widget == self.inactive_mods_listbox:
            index = widget.curselection()
            if not index:
                return
            index = index[0]  # Get the first selected index
            mod_name = widget.get(index)
            if not mod_name:
                return
            mod = self.manager.mod_by_name(mod_name)
            if not mod:
                return
            self.display_mod_info(mod)

    def display_mod_info(self, mod: Mod):
        self.clear_info()
        core_frame = Frame(self.info_frame)
        core_frame.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        core_frame.columnconfigure(0, weight=0)
        core_frame.columnconfigure(1, weight=1)
        core_frame.rowconfigure(0, weight=1)

        half_width = int(self.info_frame_width / 2)
        # Create fixed-size image container
        image_container = Frame(core_frame, width=half_width, height=210)
        image_container.grid(row=0, column=0, padx=5, pady=5, sticky=NSEW)
        image_container.grid_propagate(False)  # Prevent resizing
        image_container.columnconfigure(0, weight=1)
        image_container.rowconfigure(0, weight=1)

        # Display image or placeholder within container
        if mod.preview_img_path and mod.preview_img_path.exists():
            try:
                img = Image.open(mod.preview_img_path)
                max_size = (300, 200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                self.current_img = ImageTk.PhotoImage(img)
                image_label = Label(image_container, image=self.current_img)
                image_label.grid(row=0, column=0, sticky=NSEW)  # Center the image
            except Exception as e:
                print(f"Error loading image: {e}")
                Label(image_container, text="Error loading image").grid(row=0, column=0, sticky=NSEW)
        else:
            Label(image_container, text="No preview image available").grid(row=0, column=0, sticky=NSEW)
        
        core_info_frame = Frame(core_frame, width=half_width, height=210)
        core_info_frame.grid(row=0, column=1, sticky=W, padx=5, pady=5)
        core_info_frame.grid_propagate(False)  # Prevent resizing
        core_data = (
            ("Name", mod.name),
            ("Version", mod.version),
            ("Author", mod.author),
            ("Date Added", mod.date_added.strftime("%b-%d-%Y %H:%M:%S")),
        )

        core_info_frame.columnconfigure(0, weight=1)
        for i, (label_text, value) in enumerate(core_data):
            individual_frame = Frame(core_info_frame)
            individual_frame.grid(row=i, column=0, sticky=W, padx=2, pady=1)
            individual_frame.columnconfigure(0, weight=1)
            individual_frame.columnconfigure(1, weight=0)
            label = Label(individual_frame, text=f"{label_text}:", anchor=W, font=("Arial", 10, "bold"))
            label.grid(row=i, column=0, sticky=W, padx=2, pady=1)
            value_label = Label(individual_frame, text=value, anchor=W, justify=LEFT)
            value_label.grid(row=i, column=1, sticky=EW, padx=2, pady=1)
        
        description_frame = Frame(self.info_frame)
        description_frame.grid(row=1, column=0, sticky=NSEW, padx=5, pady=5)
        description_frame.columnconfigure(0, weight=1)
        description_frame.rowconfigure(0, weight=1)
        description_text = Text(description_frame, wrap=WORD, height=10, width=50)
        description_text.insert(END, mod.description)
        description_text.config(state=DISABLED)  # Make it read-only
        description_text.grid(row=0, column=0, sticky=NSEW, padx=5, pady=5)
        description_scrollbar = ttk.Scrollbar(description_frame, command=description_text.yview)
        description_scrollbar.grid(row=0, column=1, sticky=NS)
        description_text.config(yscrollcommand=description_scrollbar.set)

        # paths
        paths_frame = Frame(self.info_frame)
        paths_frame.grid(row=2, column=0, sticky=NSEW, padx=5, pady=5)
        paths_frame.columnconfigure(0, weight=1)
        paths_frame.rowconfigure(0, weight=1)
        max_len = 70
        part_len = int(max_len/2-2)
        mod_path = mod.path.as_posix() if len(mod.path.as_posix()) < max_len else f"{mod.path.as_posix()[:part_len]}...{mod.path.as_posix()[-part_len:]}"
        mod_url = (mod.web_url if len(mod.web_url) < max_len else f"{mod.web_url[:part_len]}...{mod.web_url[-part_len:]}") if mod.web_url else "N/A"
        mod_steam_url = (mod.steam_url if len(mod.steam_url) < max_len else f"{mod.steam_url[:part_len]}...{mod.steam_url[-part_len:]}") if mod.steam_url else "N/A"
        paths = (
            ("Local Path", mod_path, mod.path.as_posix()),
            ("Web URL", mod_url, mod.web_url),
            ("Steam URL", mod_steam_url, mod.steam_url),
        )
        min_width = max(len(label_text) for label_text, _, _ in paths) + 2  # +2 for padding
        for i, (label_text, display_value, real_value) in enumerate(paths):
            individual_frame = Frame(paths_frame)
            individual_frame.grid(row=i, column=0, sticky=W, padx=5, pady=1)
            individual_frame.columnconfigure(0, weight=0)
            individual_frame.columnconfigure(1, weight=1)
            label = Label(individual_frame, text=f"{label_text}:", anchor=W, font=("Arial", 10, "bold"), width=min_width)
            label.grid(row=i, column=0, sticky=W, padx=5)
            value_label = Label(individual_frame, text=display_value, anchor=W, justify=LEFT)
            value_label.grid(row=i, column=1, sticky=W, padx=5)
            value_label.bind("<Button-3>", lambda e, v=real_value: self.copy_context_menu(e, v))
        
    def copy_context_menu(self, event, value):
        """Create a context menu for paths"""
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="Copy", command=lambda: self.copy_to_clipboard(value))
        context_menu.post(event.x_root, event.y_root)
    
    def kenshi_path_context_menu(self, event):
        """Create a context menu for Kenshi paths"""
        context_menu = Menu(self.root, tearoff=0)
        context_menu.add_command(label="SET Kenshi Dir", command=lambda: self.select_kenshi_folder_dialog())
        context_menu.add_command(label="Copy Path", command=lambda: self.copy_to_clipboard(self.manager.kenshi_dir.as_posix()))
        context_menu.post(event.x_root, event.y_root)

    def select_kenshi_folder_dialog(self):
        kenshi_dir = select_kenshi_folder()
        if kenshi_dir:
            self.manager = Manager(kenshi_dir)
            self.update_mod_lists()
            self.clear_info()
            self.stop_blinking()
            self.stop_blinking_reload()

    def clear_info(self):
        """Clear the mod information display"""
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        self.current_img = None

    def handle_mod_rightclick(self, event):
        """Handle right-click context menu for mods"""
        widget = event.widget
        index = widget.nearest(event.y)
        if not self.was_click_on_item(event, widget):
            return
        mod_name = widget.get(index)
        mod = self.manager.mod_by_name(mod_name)

        if isinstance(widget, Listbox):
            widget.selection_clear(0, END)
            widget.selection_set(index)
            widget.activate(index)
            self.display_mod_info(mod)
        
        if index < 0:
            return
        
        # Create context menu
        context_menu = Menu(self.root, tearoff=0)
        # commands: open folder, open URL in browser, open URL in Steam, copy mod path to clipboard, copy URL to clipboard
        if mod:
            # if item has ERROR background add "Load prerequisites" command
            if widget.itemcget(index, 'bg') == COLOR_ERROR:
                context_menu.add_command(label="Load Prerequisites", command=lambda: self.load_prerequisites(mod))
                context_menu.add_separator()
            context_menu.add_command(label="Open Mod Folder", command=lambda: self.open_mod_folder(mod))
            context_menu.add_command(label="Copy Mod Path", command=lambda: self.copy_mod_path(mod))
            context_menu.add_separator()
            
            if mod.web_url:
                context_menu.add_command(label="Open URL in Browser", command=lambda: self.open_url(mod))
            if mod.steam_url:
                context_menu.add_command(label="Open URL in Steam", command=lambda: self.open_steam_url(mod))
            if mod.web_url:
                context_menu.add_command(label="Copy URL", command=lambda: self.copy_url(mod))
        
        # Show the context menu
        context_menu.post(event.x_root, event.y_root)

    def open_mod_folder(self, mod: Mod):
        """Open the mod's folder in the file explorer"""
        if mod.path.is_file():
            path = mod.path.parent
        else:
            path = mod.path
        self.open_folder(path)

    def open_folder(self, path):
        """Open folder in the file explorer"""
        import os
        path = Path(path)
        os.startfile(path)

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
        self.copy_to_clipboard(mod.path.parent.as_posix())

    def copy_url(self, mod: Mod):
        """Copy the mod's URL to the clipboard"""
        if mod.web_url:
            self.copy_to_clipboard(mod.web_url)
        
    # ======================
    # MOD LIST OPERATIONS
    # ======================

    def load_prerequisites(self, mod: Mod):
        """Load prerequisites for the given mod"""
        not_available = self.manager.load_prerequisites(mod)
        if not_available:
            missing_mods_str = "\n".join(not_available)
            messagebox.showwarning(
                "Missing Prerequisites",
                f"The following mods could not be loaded:\n{missing_mods_str}\n"
            )
        self.update_mod_lists()
        self.start_blinking()
    
    def sort_active_mods(self):
        prev_order = self.manager.active_mods.copy()
        missing_reqs = self.manager.sort_active_mods()
        if missing_reqs:
            missing_mods_str = "\n".join(missing_reqs)
            messagebox.showwarning(
                "Missing Requirements",
                f"The following mods are missing:\n{missing_mods_str}\n\n"
                "Please check the mod requirements and resolve any issues."
            )
        # if sorted_mods is not the same as current active mods, start blinking the save button
        if prev_order != self.manager.active_mods:
            self.start_blinking()
        self.update_mod_lists()

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
            prev_order = self.manager.active_mods.copy()
            with open(file_path, 'r') as f:
                mod_names = f.read().splitlines()
                self.manager.active_mods.clear()
                for mod_name in mod_names:
                    mod = next((m for m in self.manager.all_mods if m.path.name == mod_name), None)
                    if mod:
                        self.manager.active_mods.append(mod)
            if prev_order != self.manager.active_mods:
                self.start_blinking()
            self.update_mod_lists()
    
    def import_modlist_from_save(self):
        try:
            save_location = self.manager.saves_location()
        except NotImplementedError:
            messagebox.showerror("Error", "Saves location is not implemented for this Kenshi version.")
            return
        except FileNotFoundError:
            messagebox.showerror("Error", f"Cannot find {Path(self.manager.kenshi_dir / 'settings.cfg').as_posix()}.\nIt knows where the saves are.")
            return
        
        from tkinter import filedialog
        # open filedialog to select a .save file or a folder containing .save files
        file_path = filedialog.askopenfilename(
            title="Select Save File or Folder",
            filetypes=[("Save files", "*.save"), ("All files", "*.*")],
            initialdir=save_location,
            multiple=False
        )

        if file_path:
            file_path = Path(file_path)
            if file_path.is_dir():
                # grab the .save file from the folder
                save_files = list(file_path.glob("*.save"))
                if not save_files:
                    messagebox.showerror("Error", "No .save files found in the selected folder.")
                    return
                file_path = save_files[0]
            mods_ready, missing_mods_names = self.manager.get_mods_from_save(file_path)
            will_load = True
            if missing_mods_names:
                missing_mods_str = "\n".join(missing_mods_names)
                will_load = messagebox.askokcancel(
                    "Missing Mods",
                    f"The following mods are missing and will not be loaded:\n{missing_mods_str}\n\n"
                    "Do you want to continue loading the available mods?"                    
                )
            if will_load and mods_ready:
                prev_order = self.manager.active_mods.copy()
                self.manager.active_mods.clear()
                self.manager.active_mods.extend(mods_ready)
                if prev_order != self.manager.active_mods:
                    self.start_blinking()
                self.update_mod_lists()

    def set_active_mods(self):
        """Save the current active mods"""
        self.manager.save_active_mods()
        self.stop_blinking()

    def clear_active_mods(self):
        """Clear the active mods list"""
        if self.manager.active_mods:
            self.manager.active_mods.clear()
            self.update_mod_lists()
            self.clear_info()
            self.start_blinking()

    def reset_modlist(self):
        """Reset the mod manager to its initial state"""
        self.manager = Manager(self.manager.kenshi_dir)
        self.update_mod_lists()
        self.clear_info()
        self.stop_blinking()
        self.stop_blinking_reload()
    
    def start_blinking(self):
        """Start blinking the save button to indicate unsaved changes"""
        if not self.needs_save:
            self.needs_save = True
            self.blink_save_button()

    def stop_blinking(self):
        self.needs_save = False
        self.root.after_cancel(self.blink_save_button)
        BG = COLOR_DARK_PRIMARY if Config().dark_mode else COLOR_LIGHT_PRIMARY
        FG = COLOR_DARK_SECONDARY if Config().dark_mode else COLOR_LIGHT_SECONDARY
        self.save_button.config(bg=BG, fg=FG)
    
    def blink_save_button(self):
        """Blink the save button to indicate unsaved changes"""
        BG1 = COLOR_SAVE_BTN_BG_READY
        BG2 = COLOR_DARK_PRIMARY if Config().dark_mode else COLOR_LIGHT_PRIMARY

        FG1 = COLOR_DARK_SECONDARY
        FG2 = COLOR_DARK_SECONDARY if Config().dark_mode else COLOR_LIGHT_SECONDARY

        if self.needs_save:
            if self.save_button.cget('bg') == BG1:
                self.save_button.config(bg=BG2, fg=FG2)
            else:
                self.save_button.config(bg=BG1, fg=FG1)
            self.root.after(1000, self.blink_save_button)

    # TODO: merge this with the save button blinking
    def start_blinking_reload(self):
        """Start blinking the reload button to indicate unsaved changes"""
        if not self.needs_reload:
            self.needs_reload = True
            self.blink_reload_button()

    def stop_blinking_reload(self):
        self.needs_reload = False
        self.root.after_cancel(self.blink_reload_button)
        BG = COLOR_DARK_PRIMARY if Config().dark_mode else COLOR_LIGHT_PRIMARY
        FG = COLOR_DARK_SECONDARY if Config().dark_mode else COLOR_LIGHT_SECONDARY
        self.reset_button.config(bg=BG, fg=FG)
        
    def blink_reload_button(self):
        """Blink the reload button to indicate unsaved changes"""
        BG1 = COLOR_RELOAD_BTN_BG_READY
        BG2 = COLOR_DARK_PRIMARY if Config().dark_mode else COLOR_LIGHT_PRIMARY

        FG1 = COLOR_DARK_SECONDARY
        FG2 = COLOR_DARK_SECONDARY if Config().dark_mode else COLOR_LIGHT_SECONDARY

        if self.needs_reload:
            if self.reset_button.cget('bg') == BG1:
                self.reset_button.config(bg=BG2, fg=FG2)
            else:
                self.reset_button.config(bg=BG1, fg=FG1)
            self.root.after(1000, self.blink_reload_button)
    
    def periodic_check_for_mods(self):
        """Periodically check for new mods and update the lists"""
        diff: ModlistDiff = self.manager.check_for_new_mods()
        if diff:
            self.start_blinking_reload()
        else:
            self.stop_blinking_reload()

        self.root.after(5000, self.periodic_check_for_mods)

    def launch_kenshi(self):
        exe = self.manager.find_kenshi_executable()
        if exe:
            try:
                # first change cwd to the Kenshi folder
                cwd = self.manager.kenshi_dir.as_posix()
                os.chdir(cwd)

                subprocess.Popen([exe], cwd=cwd)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to launch Kenshi: {e}")
        else:
            self.launch_kenshi_button.config(state=DISABLED)


if __name__ == "__main__":
    kenshi_folder = r"E:\SteamLibrary\steamapps\common\Kenshi"
    
    manager = Manager(kenshi_folder)

    start_gui(manager)