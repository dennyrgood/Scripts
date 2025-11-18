#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import shlex
import os
import datetime 
import sys 
import threading 
import queue 
import time

class MyEverythingApp:
    
    # --- 1. CONFIGURATION CONSTANTS (Leaner, Easier to Modify) ---
    
    # Defines Treeview column properties: (header_text, width, internal_data_key)
    COLUMN_SETUP = {
        "#0": {"text": "File Name", "width": 200, "data_key": "Name"},
        "Folder": {"text": "Folder", "width": 250, "data_key": "Folder"},
        "Size": {"text": "Size", "width": 80, "data_key": "Size_Bytes"},
        "Modified": {"text": "Modified Date", "width": 120, "data_key": "Modified_Timestamp"},
        "Accessed": {"text": "Accessed Date", "width": 120, "data_key": "Accessed_Timestamp"},
        "Changed": {"text": "Changed Date", "width": 120, "data_key": "Changed_Timestamp"},
    }
    
    # Maps GUI variables to their corresponding 'find' command flags.
    FIND_FILTERS = [
        ("file_type", "-type"),
        ("size_val", "-size"),
        ("mtime_val", "-mtime"),
        ("atime_val", "-atime"),
        ("ctime_val", "-ctime"),
    ]
    
    # Visual constants
    ERROR_BG_COLOR = '#FFEDED'  # Pale red/pink background for error box
    ERROR_FG_COLOR = 'black'    # Explicit black foreground for text contrast

    # Limit results to prevent UI freeze (None = no limit)
    MAX_DISPLAYED_RESULTS = None  # or set to an int like 10000
    
    def __init__(self, master):
        self.master = master
        master.title("MyEverything: macOS Find GUI")
        # Set geometry for better visibility of results and error box
        master.geometry("1000x950")

        # --- Variables (Filter Inputs) ---
        self.search_name = tk.StringVar(value="*")
        self.start_path = tk.StringVar(value=os.path.expanduser("~"))
        self.case_insensitive = tk.BooleanVar(value=True) 
        self.file_type = tk.StringVar(value="f") 
        self.size_val = tk.StringVar(value="")
        self.mtime_val = tk.StringVar(value="")
        self.atime_val = tk.StringVar(value="")
        self.ctime_val = tk.StringVar(value="")
        self.other_args = tk.StringVar(value="") 
        
        # --- Threading/Process Variables ---
        self.search_thread = None
        self.process = None # Holds the subprocess.Popen instance (SHARED)
        self.output_queue = queue.Queue() # Thread-safe queue for result communication
        self.temp_stderr = "" # Temporary holder for stderr output
        self._running = False # flag to indicate an active search
        
        # Internal dictionary to store file metadata (raw size/timestamps) for accurate sorting
        self.file_data = {}

        # --- Build GUI ---
        self._create_widgets()

    def _create_widgets(self):
        """Builds all GUI components, consolidating filters and styling the status bar.""\