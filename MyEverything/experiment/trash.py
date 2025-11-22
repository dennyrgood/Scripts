 import os
 import sys
 from tkinter import *
 from tkinter import ttk, filedialog, messagebox
 from datetime import datetime
 from queue import Queue
 from subprocess import Popen, PIPE, STDOUT, run
 import shlex

 class MyEverythingApp:
     FIND_FILTERS = [
         ("start_path", None),
         ("search_name", "search_name"),
         ("case_insensitive", False),
         ("file_suffix", ""),
         ("directory_contains", ""),
         # ... and so on for all the variables as in your original code
     ]
     
     def __init__(self, root):
         self.root = root
         self.start_path = StringVar()
         self.search_name = StringVar()
         self.case_insensitive = BooleanVar()
         
         self.FIND_FILTERS = [
             ("start_path", "start_path"),
             # ... add all the filters and variables as you have them in your 
 original code
         ]
         
         root.title("My Everything")
         root.geometry("800x600")

         frame = ttk.Frame(root)
         frame.pack(fill=BOTH, expand=YES)

         # Start Path
         self.start_path_label = Label(frame, text="Start Directory:")
         self.start_path_label.grid(row=0, column=0, padx=10, pady=(2, 0))
         start_dir_entry = Entry(frame, textvariable=self.start_path, width=40)
         self.select_button = Button(frame, text="Select", 
 command=self._select_path)

         # Case Insensitive Search
         CaseInsensitiveCheckVar = BooleanVar()
         case_insensitive_check_box = Checkbutton(frame, 
 variable=CaseInsensitiveCheckVar, command=lambda: setattr(self, 
 "case_insensitive", CaseInsensitiveCheckVar.get()))

         # Filter Name and other filters as in your original code

         # Buttons
         button_frame = Frame(frame)
         self.search_button = Button(button_frame, text="Search", 
 command=self._do_everything_search)

         # Treeview for Results
         tree_frame = Frame(root)
         columns = ('Name', 'Size', 'Modified', 'Accessed', 'Changed')
         self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings')

         vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
         hsb = ttk.Scrollbar(frame, orient="horizontal", 
 command=self.tree.xview)
         
         # Other widgets for Filters and Results display
         self._create_widgets()

     def _do_everything_search(self):
         root.update_idletasks()
         self._build_find_command()
     
     def _select_path(self):
         folder_selected = 
 filedialog.askdirectory(initialdir=self.start_path.get())
         if folder_selected:
             self.start_path.set(folder_selected)

     def _create_widgets(self):
         # Create and place all the widgets in their respective positions
         self.start_path_label.grid(row=0, column=0, padx=10, pady=(2, 0))
         start_dir_entry = Entry(frame, textvariable=self.start_path, width=40)
         start_dir_entry.grid(row=0, column=1, padx=10, pady=(2, 0), sticky=W)

         self.select_button.grid(row=0, column=2, padx=10, pady=(2, 0))

         # Case Insensitive Search
         case_insensitive_check_box = Checkbutton(frame, 
 variable=self.case_insensitive)
         case_insensitive_check_box.grid(row=1, column=0, columnspan=3, 
 padx=10, pady=(2, 0), sticky=W)

         # Other widgets for filters as needed

         Button(self.tree_frame, text="Search", 
 command=self._do_everything_search).pack(side=TOP)
         
         vsb['command'] = self.tree.yview
         hsb['command'] = self.tree.xview
         self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

         # Set the column headers for the tree view
         for col in columns:
             self.tree.heading(col, text=col)
             self.tree.column(col, stretch=YES, anchor='center' if col != 
 'Name' else W)
         
         self.tree.grid(row=2, column=0, sticky=(N, S, E, W), padx=10, pady=(5,
  0))
         vsb.pack(side=RIGHT, fill=Y, ipady=80)  # Adjust the height of 
 scrollbars
         hsb.pack(fill=X)
         
         self.tree_frame.grid(row=3, column=0, columnspan=6)

     def _build_find_command(self):
         command = ["find", self.start_path.get()]

         for var_name, flag in self.FIND_FILTERS:
             var_instance = getattr(self, var_instance, None)
             if var_instance and var_instance.get().strip():
                 command.extend([flag, var_instance.get().strip()])

         other_args_val = self.other_args.get().strip()
         if other_args_val:
             try:
                 extra_args = shlex.split(other_args_val)
                 command.extend(extra_args)
             except ValueError:
                 self._log_error("Warning: shlex failed to parse 'Other 
 Arguments'. Using simple split.")
                 command.extend(other_args_val.split())
         
         command.append("-print")
         
         return command

     # Insert results into the tree, log errors, and other helper methods as in
  your original code
     
 if __name__ == "__main__":
     root = Tk()
     app = MyEverythingApp(root)
     root.mainloop()
