import tkinter as tk
from tkinter import messagebox
from loguru import logger
from typing import Optional

def _get_hidden_root():
    """Creates and returns a hidden Tk root window for dialogs."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    return root

def show_info(title: str, message: str, parent=None):
    """Shows an information dialog."""
    temp_root = None
    if not parent:
        temp_root = _get_hidden_root()
        parent = temp_root
        
    messagebox.showinfo(title, message, parent=parent)
    
    if temp_root:
        temp_root.destroy()

def show_warning(title: str, message: str, parent=None):
    """Shows a warning dialog."""
    temp_root = None
    if not parent:
        temp_root = _get_hidden_root()
        parent = temp_root
        
    messagebox.showwarning(title, message, parent=parent)
    
    if temp_root:
        temp_root.destroy()

def show_error(title: str, message: str, parent=None):
    """Shows an error dialog."""
    temp_root = None
    if not parent:
        temp_root = _get_hidden_root()
        parent = temp_root
        
    messagebox.showerror(title, message, parent=parent)
    
    if temp_root:
        temp_root.destroy()

def ask_yes_no(title: str, message: str, parent=None) -> bool:
    """Shows a yes/no dialog and returns the result."""
    temp_root = None
    if not parent:
        temp_root = _get_hidden_root()
        parent = temp_root
        
    result = messagebox.askyesno(title, message, parent=parent)
    
    if temp_root:
        temp_root.destroy()
    return result

def ask_config_gui(current_vals, on_save_callback):
    """Centrally launches the Config GUI."""
    from utils.gui import ConfigGUI
    gui = ConfigGUI(current_vals, on_save_callback)
    
    # Optional: Setup close protocol if needed here
    def on_close():
        gui.root.quit()
        gui.root.destroy()
        
    gui.root.protocol("WM_DELETE_WINDOW", on_close)
    gui.run()
