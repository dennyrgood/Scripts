#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import shlex
import os

class MyEverythingApp:
    def __init__(self, master):
        self.master = master
        master.title("MyEverything: macOS Find GUI")
        master.geometry("800x600")

        # --- Variables ---
        self.search_name = tk.StringVar(value="*") # Default search pattern
        self.start_path = tk.StringVar(value=os.path.expanduser("~")) # Default to Home Directory
        self.case_insensitive = tk.BooleanVar(value=True) # Default to -iname
        self.file_type = tk.StringVar(value="f") # Default to file type 'f'

        # --- Build GUI ---
        self._create_widgets()

    def _create_widgets(self):
        # 1. Input Frame (Search Path and Pattern)
        input_frame = ttk.LabelFrame(self.master, text="🔍 Search Parameters")
        input_frame.pack(padx=10, pady=10, fill="x")

        # Start Path
        ttk.Label(input_frame, text="Start Path:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        path_entry = ttk.Entry(input_frame, textvariable=self.start_path)
        path_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(input_frame, text="Browse", command=self._select_path).grid(row=0, column=2, padx=5, pady=5)
        
        # Search Pattern (-name / -iname)
        ttk.Label(input_frame, text="-name / -iname:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ttk.Entry(input_frame, textvariable=self.search_name).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Checkbutton(input_frame, text="Case Insensitive (-iname)", variable=self.case_insensitive).grid(row=1, column=2, padx=5, pady=5)

        # Configure columns for input_frame
        input_frame.grid_columnconfigure(1, weight=1)

        # 2. Options Frame (File Type)
        options_frame = ttk.LabelFrame(self.master, text="⚙️ Find Options")
        options_frame.pack(padx=10, pady=5, fill="x")
        
        ttk.Label(options_frame, text="File Type (-type):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(options_frame, text="File (-type f)", variable=self.file_type, value="f").grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(options_frame, text="Directory (-type d)", variable=self.file_type, value="d").grid(row=0, column=2, padx=5, pady=5)
        ttk.Radiobutton(options_frame, text="Any Type (skip -type)", variable=self.file_type, value="").grid(row=0, column=3, padx=5, pady=5)
        
        # 3. Execute Button
        ttk.Button(self.master, text="▶️ Run Find Command", command=self.run_find).pack(pady=5, padx=10, fill="x")

        # 4. Results Area
        ttk.Label(self.master, text="Results:").pack(padx=10, pady=2, anchor="w")
        
        # Text widget for results with a scrollbar
        results_frame = ttk.Frame(self.master)
        results_frame.pack(padx=10, pady=5, fill="both", expand=True)
        
        self.results_text = tk.Text(results_frame, wrap="none", height=15)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        h_scrollbar = ttk.Scrollbar(results_frame, orient="horizontal", command=self.results_text.xview)
        
        self.results_text.config(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.results_text.pack(side="left", fill="both", expand=True)

    def _select_path(self):
        """Opens a dialog to select the starting directory."""
        folder_selected = filedialog.askdirectory(initialdir=self.start_path.get())
        if folder_selected:
            self.start_path.set(folder_selected)

    def _build_find_command(self):
        """Constructs the full 'find' command based on GUI inputs."""
        
        # Initial command structure: find [path]
        command = [
            "find",
            self.start_path.get()
        ]

        # Add -type if a specific file type is selected
        file_type_val = self.file_type.get()
        if file_type_val:
            command.extend(["-type", file_type_val])
        
        # Add -name or -iname
        search_arg = "-iname" if self.case_insensitive.get() else "-name"
        command.extend([search_arg, self.search_name.get()])
        
        return command

    def run_find(self):
        """Executes the constructed find command and displays output."""
        
        # Clear previous results
        self.results_text.delete(1.0, tk.END)
        
        try:
            find_command = self._build_find_command()
            
            # Display command being run
            self.results_text.insert(tk.END, f"Running command: {' '.join(shlex.quote(arg) for arg in find_command)}\n\n", 'info')
            
            # Execute the command
            process = subprocess.run(
                find_command, 
                capture_output=True, 
                text=True, 
                check=False, # Don't raise error on non-zero exit code (like permission denied)
                timeout=300 # 5 minute timeout
            )

            # Display results (stdout)
            if process.stdout:
                self.results_text.insert(tk.END, process.stdout)
            
            # Display errors (stderr)
            if process.stderr:
                self.results_text.insert(tk.END, f"\n--- ERRORS ---\n{process.stderr}", 'error')

            self.results_text.tag_config('info', foreground='blue')
            self.results_text.tag_config('error', foreground='red')

        except FileNotFoundError:
            self.results_text.insert(tk.END, "Error: The 'find' command was not found.", 'error')
        except subprocess.TimeoutExpired:
            self.results_text.insert(tk.END, "Error: Command timed out after 5 minutes.", 'error')
        except Exception as e:
            self.results_text.insert(tk.END, f"An unexpected error occurred: {e}", 'error')

if __name__ == "__main__":
    root = tk.Tk()
    app = MyEverythingApp(root)
    root.mainloop()
