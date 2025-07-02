
from tkinter import *

from mod import Mod


def mod_select_dialog(gui, left_mods, right_mods=[], ok_btn_lbl="OK", cancel_btn_lbl="Cancel"):
    """
    Creates a dialog window.
    Each item in the list will have a checkbox next to it.
    When The Ok button is clicked, the selected Mods will be returned as a list.
    :param left_list: List of Mods to display on the left side.
    :param right_list: List of Mods to display on the right side (optional).
    :param ok_btn_lbl: Label for the OK button.
    :param cancel_btn_lbl: Label for the Cancel button.
    :return: List of selected Mods.
    """
    dialog = _ModSelectDialog(gui, left_mods, right_mods, ok_btn_lbl, cancel_btn_lbl)
    gui.root.wait_window(dialog.dialog)  # Wait for the dialog to close
    return dialog.get_selected_items()


class _ModSelectDialog:
    def __init__(self, gui, left_mods, right_mods=[], ok_btn_lbl="OK", cancel_btn_lbl="Cancel"):
        self.manager = gui.manager
        self.master = gui.root
        self.left_mods = left_mods
        self.right_mods = right_mods
        self.ok_btn_lbl = ok_btn_lbl
        self.cancel_btn_lbl = cancel_btn_lbl

        self.selected_items = []

        self.create_widgets()

    def create_widgets(self):
        self.dialog = Toplevel(self.master, width=400, height=300)
        self.dialog.title("Select Mods")
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        self.dialog.minsize(400, 300)

        self.left_frame = Frame(self.dialog)
        self.left_frame.pack(side=LEFT, padx=10, pady=10, fill=BOTH, expand=True)

        self.right_frame = Frame(self.dialog)
        self.right_frame.pack(side=RIGHT, padx=10, pady=10, fill=BOTH, expand=True)

        self.left_checkboxes = []
        self.right_checkboxes = []
        self.create_checkboxes(self.left_frame, self.left_mods, self.left_checkboxes)
        self.create_checkboxes(self.right_frame, self.right_mods, self.right_checkboxes, checked=True)

        self.ok_button = Button(self.dialog, text=self.ok_btn_lbl, command=self.on_ok)
        self.ok_button.pack(side=LEFT, padx=10, pady=10)
        self.cancel_button = Button(self.dialog, text=self.cancel_btn_lbl, command=self.on_cancel)
        self.cancel_button.pack(side=RIGHT, padx=10, pady=10)

    def create_checkboxes(self, frame, items, checkboxes, checked=False):
        right = True if frame == self.right_frame else False
        label_side = RIGHT if right else LEFT
        ceckbox_side = LEFT if right else RIGHT
        for item in items:
            item_frame = Frame(frame, borderwidth=2, relief="ridge")
            item_frame.pack(anchor=W, padx=5, pady=2, fill=X)
            var = BooleanVar(value=checked)
            label = Label(item_frame, text=item.name if isinstance(item, Mod) else item)
            label.pack(side=label_side)
            checkbox = Checkbutton(item_frame, variable=var, fg="black")
            checkbox.pack(side=ceckbox_side)
            checkboxes.append((item, var))

    def on_ok(self):
        self.selected_items = [item for item, var in self.left_checkboxes if var.get()]
        self.selected_items += [item for item, var in self.right_checkboxes if var.get()]
        self.dialog.destroy()

    def on_cancel(self):
        self.selected_items = None # to distinguish from []
        self.dialog.destroy()

    def on_close(self):
        self.selected_items = None
        self.dialog.destroy()

    def get_selected_items(self):
        if self.selected_items is None:
            return None
        return self.selected_items.copy()
    