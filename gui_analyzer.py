import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinterdnd2 import DND_FILES, TkinterDnD
import subprocess
import os
import pathlib
import threading
import queue
import sys
from tkinter import filedialog

# --- Configuration ---
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
VENV_DIR = SCRIPT_DIR / ".venv"
MAIN_PY_SCRIPT = SCRIPT_DIR / "main.py"

# Determine the Python executable path within the venv
if sys.platform == "win32":
    VENV_PYTHON_EXEC = VENV_DIR / "Scripts" / "python.exe"
else:
    VENV_PYTHON_EXEC = VENV_DIR / "bin" / "python"
# --- End Configuration ---

class BlendAnalyzerApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Blend File Analyzer")
        self.geometry("800x800")

        self.thread_queue = queue.Queue()
        self.blender_executable_path = None

        # Styling
        style = ttk.Style(self)
        style.theme_use('clam') # Or 'alt', 'default', 'classic'

        style.configure("TLabel", padding=10, font=("Segoe UI", 10))
        style.configure("TButton", padding=10, font=("Segoe UI", 10))
        style.configure("Drop.TLabel", background="lightgrey", relief="solid", borderwidth=2, anchor="center", font=("Segoe UI", 12, "bold"))

        # Blender Executable Selector
        self.blender_path_button = ttk.Button(self, text="Select Blender Executable", command=self.select_blender_executable)
        self.blender_path_button.pack(fill=tk.X, padx=20, pady=(10, 0))

        self.blender_path_label = ttk.Label(self, text="Blender Executable: (default: blender in PATH)")
        self.blender_path_label.pack(fill=tk.X, padx=20, pady=(0, 5))

        # LMStudio API and Model Name with defaults
        self.lmstudio_api_var = tk.StringVar(value="http://localhost:1234/v1")
        self.lmstudio_model_var = tk.StringVar(value="qwen3-1.7b")  # "qwen3-4b", "qwen3-1.7b"

        # LMStudio API Address
        lmstudio_api_frame = ttk.Frame(self)
        lmstudio_api_frame.pack(fill=tk.X, padx=20, pady=(5, 0))
        ttk.Label(lmstudio_api_frame, text="LMStudio API URL:").pack(side=tk.LEFT)
        self.lmstudio_api_entry = ttk.Entry(lmstudio_api_frame, textvariable=self.lmstudio_api_var, width=30)
        self.lmstudio_api_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # LMStudio Model Name
        lmstudio_model_frame = ttk.Frame(self)
        lmstudio_model_frame.pack(fill=tk.X, padx=20, pady=(0, 5))
        ttk.Label(lmstudio_model_frame, text="LMStudio Model Name:").pack(side=tk.LEFT)
        self.lmstudio_model_entry = ttk.Entry(lmstudio_model_frame, textvariable=self.lmstudio_model_var, width=30)
        self.lmstudio_model_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        # --- END MOVE ---

        # Drop Target
        self.drop_target_label = ttk.Label(self, text="Drag and Drop .blend file here", style="Drop.TLabel")
        self.drop_target_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.drop_target_label.drop_target_register(DND_FILES)
        self.drop_target_label.dnd_bind('<<Drop>>', self.handle_drop)

        # Status Area
        self.status_label = ttk.Label(self, text="Status: Waiting for .blend file...")
        self.status_label.pack(fill=tk.X, padx=20, pady=(0, 5))

        self.output_text = scrolledtext.ScrolledText(self, height=10, wrap=tk.WORD, font=("Courier New", 9))
        self.output_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.output_text.configure(state='disabled')

        self.check_venv_and_script()
        self.after(100, self.process_queue)

    def check_venv_and_script(self):
        if not VENV_PYTHON_EXEC.is_file():
            self.update_status(f"ERROR: Virtual environment Python not found at {VENV_PYTHON_EXEC}\nPlease run setup_env.bat/sh first.", error=True)
            self.drop_target_label.dnd_unbind('<<Drop>>') # Disable drop if venv is missing
            return False
        if not MAIN_PY_SCRIPT.is_file():
            self.update_status(f"ERROR: main.py script not found at {MAIN_PY_SCRIPT}", error=True)
            self.drop_target_label.dnd_unbind('<<Drop>>') # Disable drop if main.py is missing
            return False
        return True
        
    def update_status(self, message, error=False):
        self.status_label.config(text=f"Status: {message}", foreground="red" if error else "black")
        self.log_output(message)

    def log_output(self, message):
        self.output_text.configure(state='normal')
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.output_text.configure(state='disabled')

    def handle_drop(self, event):
        filepath_str = event.data
        # TkinterDND often wraps paths in curly braces if they contain spaces
        if filepath_str.startswith('{') and filepath_str.endswith('}'):
            filepath_str = filepath_str[1:-1]

        filepath = pathlib.Path(filepath_str)

        if not filepath.is_file():
            self.update_status(f"Error: '{filepath.name}' is not a valid file.", error=True)
            return
        
        if filepath.suffix.lower() != ".blend":
            self.update_status(f"Error: '{filepath.name}' is not a .blend file.", error=True)
            return

        self.update_status(f"Processing '{filepath.name}'...")
        self.output_text.configure(state='normal')
        self.output_text.delete('1.0', tk.END) # Clear previous output
        self.output_text.configure(state='disabled')
        self.log_output(f"Starting analysis for: {filepath_str}")

        # Run analysis in a separate thread
        analysis_thread = threading.Thread(target=self.run_analysis_script, args=(filepath_str,), daemon=True)
        analysis_thread.start()

    def select_blender_executable(self):
        file_path = filedialog.askopenfilename(
            title="Select Blender Executable",
            filetypes=[("Blender Executable", "blender.exe" if sys.platform == "win32" else "blender"), ("All Files", "*.*")]
        )
        if file_path:
            self.blender_executable_path = file_path
            self.blender_path_label.config(text=f"Blender Executable: {file_path}")
        else:
            self.blender_executable_path = None
            self.blender_path_label.config(text="Blender Executable: (default: blender in PATH)")
        # REMOVE the LMStudio input creation from here

    def run_analysis_script(self, blend_filepath_str):
        if not self.check_venv_and_script():
            self.thread_queue.put(("ERROR: Environment/script check failed before analysis.", True))
            return

        command = [
            str(VENV_PYTHON_EXEC),
            str(MAIN_PY_SCRIPT),
            "--filepath",
            blend_filepath_str
        ]
        if self.blender_executable_path:
            command += ["--blender-exec", self.blender_executable_path]
        # Add LMStudio API and model if provided
        lmstudio_api = self.lmstudio_api_var.get().strip()
        lmstudio_model = self.lmstudio_model_var.get().strip()
        if lmstudio_api:
            command += ["--lmstudio-api", lmstudio_api]
        if lmstudio_model:
            command += ["--lmstudio-model", lmstudio_model]

        self.thread_queue.put((f"Executing: {' '.join(command)}", False))

        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
            
            # Stream stdout
            for line in iter(process.stdout.readline, ''):
                self.thread_queue.put((line.strip(), False))
            process.stdout.close()

            # Stream stderr
            for line in iter(process.stderr.readline, ''):
                self.thread_queue.put((f"STDERR: {line.strip()}", True)) # Mark stderr lines as errors
            process.stderr.close()
            
            return_code = process.wait()

            if return_code == 0:
                self.thread_queue.put((f"Analysis of '{pathlib.Path(blend_filepath_str).name}' completed successfully. HTML report should be generated.", False))
            else:
                self.thread_queue.put((f"Analysis of '{pathlib.Path(blend_filepath_str).name}' failed with exit code {return_code}.", True))
        except Exception as e:
            self.thread_queue.put((f"Exception during analysis: {e}", True))

    def process_queue(self):
        try:
            while True:
                message, is_error = self.thread_queue.get_nowait()
                if "STDERR:" in message or is_error: # A bit redundant but covers both
                    self.log_output(message) # Log all messages
                    # Update status only for summary messages or critical errors
                    if "failed" in message.lower() or "exception" in message.lower() or "error:" in message.lower():
                         self.status_label.config(text=f"Status: {message.splitlines()[0]}", foreground="red")
                else:
                    self.log_output(message)
                    # Update status for key messages
                    if "processing" in message.lower() or "completed successfully" in message.lower() or "waiting" in message.lower():
                         self.status_label.config(text=f"Status: {message.splitlines()[0]}", foreground="black")

        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue) # Check queue again after 100ms

if __name__ == '__main__':
    app = BlendAnalyzerApp()
    app.mainloop()