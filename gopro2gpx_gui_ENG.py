import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import argparse
import sys
import time
import csv
import re
import subprocess
import tempfile
import webbrowser
import configparser

# Helper class to redirect stdout to a Tkinter Text widget
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, s):
        if s.strip() != "":
            # Use after to ensure the update is done in the main thread
            self.widget.after(0, lambda: self.widget.insert("end", s))
            self.widget.after(0, lambda: self.widget.see("end"))

    def flush(self):
        pass

# Function to get the absolute path to a resource, considering frozen mode (onefile)
def resource_path(relative_path):
    """
    Returns the absolute path to the resource given by 'relative_path', using sys._MEIPASS in frozen mode.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Import main_core function from the corresponding module
try:
    from gopro2gpx.gopro2gpx import main_core
except ImportError:
    try:
        import gopro2gpx.gopro2gpx
        main_core = gopro2gpx.gopro2gpx.main_core
    except ImportError:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from gopro2gpx.gopro2gpx import main_core

class GoPro2GPXGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GoPro2gpx - Graphical User Interface")
        # Set initial size according to the active tab (Descriptor will be smaller)
        self.geometry("800x400")
        
        # Persistent configuration: Read settings from config.ini.
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
        self.config_parser = configparser.ConfigParser()
        if os.path.exists(self.config_path):
            self.config_parser.read(self.config_path)
        else:
            self.config_parser['Paths'] = {}
        
        # If no last directory is saved, initialize to "C:\\"
        self.last_video_dir = self.config_parser['Paths'].get('last_video_dir', "C:\\")
        self.last_output_dir = self.config_parser['Paths'].get('last_output_dir', "C:\\")
        
        # Variables for storing paths and options
        self.input_dir = tk.StringVar()
        self.output_dir = tk.StringVar()
        
        # Default options: Verbose mode and skip erroneous points enabled.
        self.verbose_var = tk.IntVar(value=1)
        self.skip_var = tk.BooleanVar(value=True)
        self.binary_var = tk.BooleanVar(value=False)
        self.skip_dop_var = tk.BooleanVar(value=False)
        self.dop_limit_var = tk.IntVar(value=2000)
        
        # Variables for the progress bar
        self.total_files = 0
        self.processed_files = 0

        # Configure Notebook widget with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        
        # Create Descriptor and Main tabs; Descriptor appears first as required
        self.descriptor_frame = ttk.Frame(self.notebook)
        self.principal_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.descriptor_frame, text="Descriptor")
        self.notebook.add(self.principal_frame, text="Main")
        
        # Bind the tab change event to adjust the window size
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)
        
        # Create widgets for tabs
        self.create_descriptor_widgets()
        self.create_principal_widgets()

        # When the application starts, select the Descriptor tab
        self.notebook.select(self.descriptor_frame)

    def on_tab_change(self, event):
        # Detect the current tab and adjust the geometry
        selected = self.notebook.select()
        if selected == str(self.descriptor_frame):
            # Smaller size for Descriptor
            self.geometry("650x300")
        elif selected == str(self.principal_frame):
            # Larger size for Main tab
            self.geometry("800x650")

    def create_principal_widgets(self):
        # --- Main Tab: Paths ---
        routes_frame = tk.LabelFrame(self.principal_frame, text="Paths")
        routes_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(routes_frame, text="Video Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(routes_frame, textvariable=self.input_dir, width=50).grid(row=0, column=1, padx=5, pady=2)
        tk.Button(routes_frame, text="Browse", command=self.select_input_dir).grid(row=0, column=2, padx=5, pady=2)
        tk.Label(routes_frame, text="Output Directory:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(routes_frame, textvariable=self.output_dir, width=50).grid(row=1, column=1, padx=5, pady=2)
        tk.Button(routes_frame, text="Browse", command=self.select_output_dir).grid(row=1, column=2, padx=5, pady=2)

        # --- Main Tab: Additional Options ---
        options_frame = tk.LabelFrame(self.principal_frame, text="Options")
        options_frame.pack(fill="x", padx=10, pady=5)
        tk.Checkbutton(options_frame, text="Verbose Mode (show detailed log)", variable=self.verbose_var).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(options_frame, text="Read data from binary file", variable=self.binary_var).grid(row=1, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(options_frame, text="Skip erroneous points (GPSFIX==0)", variable=self.skip_var).grid(row=2, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Checkbutton(options_frame, text="Skip points with high precision (GPSP > limit)", variable=self.skip_dop_var).grid(row=3, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        tk.Label(options_frame, text="GPSP Limit:").grid(row=4, column=0, sticky="w", padx=5, pady=2)
        tk.Entry(options_frame, textvariable=self.dop_limit_var, width=10).grid(row=4, column=1, sticky="w", padx=5, pady=2)

        # --- Main Tab: Output Format and Camera Type Options ---
        output_type_frame = tk.LabelFrame(self.principal_frame, text="Output Format")
        output_type_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(output_type_frame, text="Select output format:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.out_format_var = tk.StringVar()
        self.out_format_combobox = ttk.Combobox(output_type_frame, textvariable=self.out_format_var, state="readonly", width=10)
        self.out_format_combobox['values'] = ("GPX", "CSV", "KML")
        self.out_format_combobox.current(0)
        self.out_format_combobox.grid(row=0, column=1, padx=5, pady=2)

        camera_frame = tk.LabelFrame(self.principal_frame, text="Camera Type")
        camera_frame.pack(fill="x", padx=10, pady=5)
        tk.Label(camera_frame, text="Select camera type:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.camera_var = tk.StringVar()
        self.camera_combobox = ttk.Combobox(camera_frame, textvariable=self.camera_var, state="readonly", width=25)
        self.camera_combobox['values'] = ("GoPRO Hero 10 or earlier", "GoPRO Hero 11 or 13")
        self.camera_combobox.current(0)
        self.camera_combobox.grid(row=0, column=1, padx=5, pady=2)

        # Button to start processing
        tk.Button(self.principal_frame, text="Process", command=self.on_process).pack(pady=10)

        # --- Main Tab: Progress Bar ---
        progress_frame = tk.LabelFrame(self.principal_frame, text="Progress")
        progress_frame.pack(fill="x", padx=10, pady=5)
        self.progress = ttk.Progressbar(progress_frame, orient='horizontal', mode='determinate')
        self.progress.pack(fill="x", padx=5, pady=5)

        # --- Main Tab: Verbose Output Text Area ---
        verbose_frame = tk.LabelFrame(self.principal_frame, text="Verbose Output")
        verbose_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.verbose_text = tk.Text(verbose_frame, height=10, wrap="word")
        self.verbose_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        verbose_scrollbar = ttk.Scrollbar(verbose_frame, orient="vertical", command=self.verbose_text.yview)
        verbose_scrollbar.pack(side="right", fill="y")
        self.verbose_text.config(yscrollcommand=verbose_scrollbar.set)

    def create_descriptor_widgets(self):
        # Use a Text widget for better formatting (larger font, bold, and links)
        self.text_descriptor = tk.Text(self.descriptor_frame, wrap="word", padx=10, pady=10, relief="flat")
        self.text_descriptor.pack(fill="both", expand=True)
        # Configure fonts
        default_font = ("Helvetica", 12)
        bold_font = ("Helvetica", 12, "bold")
        self.text_descriptor.configure(font=default_font)
        
        # Configure tags for bold and hyperlinks
        self.text_descriptor.tag_configure("bold", font=bold_font)
        self.text_descriptor.tag_configure("hyperlink", foreground="blue", underline=1)
        
        # Function to handle hyperlink clicks
        def click_link(url):
            webbrowser.open_new(url)
        
        # Insert enriched content in the Descriptor tab
        self.text_descriptor.insert("end", "Application Overview:\n", "bold")
        self.text_descriptor.insert("end", "\nThis application extracts GPS data from videos recorded with GoPro cameras and generates files in GPX, CSV, or KML formats. The processing runs in the background and features an intuitive interface that shows progress.\n\n")
        
        self.text_descriptor.insert("end", "About GoPro2gpx:\n", "bold")
        self.text_descriptor.insert("end", "\n• Main code developed by ")
        # Insert hyperlink for the first repository
        self.text_descriptor.insert("end", "https://github.com/juanmcasillas", "hyperlink")
        self.text_descriptor.tag_bind("hyperlink", "<Button-1>", lambda e, url='https://github.com/juanmcasillas': click_link(url))
        self.text_descriptor.insert("end", " and contributors.\n")
        self.text_descriptor.insert("end", "• Windows GUI created by German Cruz R ")
        self.text_descriptor.insert("end", "https://github.com/germancruzram", "hyperlink_secondary")
        self.text_descriptor.tag_configure("hyperlink_secondary", foreground="blue", underline=1)
        self.text_descriptor.tag_bind("hyperlink_secondary", "<Button-1>", lambda e, url='https://github.com/germancruzram': click_link(url))
        self.text_descriptor.insert("end", ".\n\n")
        
        self.text_descriptor.insert("end", "version 1.0 - 2025", "bold")
        # Set the Text widget as read-only
        self.text_descriptor.configure(state="disabled")

    def select_input_dir(self):
        # If a folder has already been selected, use it as the initial directory.
        # Otherwise, start in the last saved directory from the configuration, defaulting to "C:\".
        initial_dir = self.input_dir.get() if self.input_dir.get() else self.last_video_dir
        directory = filedialog.askdirectory(title="Select Video Directory", initialdir=initial_dir)
        if directory:
            self.input_dir.set(directory)
            self.last_video_dir = directory
            self.config_parser['Paths']['last_video_dir'] = directory
            with open(self.config_path, 'w') as configfile:
                self.config_parser.write(configfile)

    def select_output_dir(self):
        # If an output folder has already been selected, use it as the initial directory.
        # Otherwise, start in the last saved directory from the configuration, defaulting to "C:\".
        initial_dir = self.output_dir.get() if self.output_dir.get() else self.last_output_dir
        directory = filedialog.askdirectory(title="Select Output Directory", initialdir=initial_dir)
        if directory:
            self.output_dir.set(directory)
            self.last_output_dir = directory
            self.config_parser['Paths']['last_output_dir'] = directory
            with open(self.config_path, 'w') as configfile:
                self.config_parser.write(configfile)

    def on_process(self):
        # Validate paths
        if not self.input_dir.get():
            messagebox.showerror("Error", "Please select the video directory.")
            return
        if not self.output_dir.get():
            messagebox.showerror("Error", "Please select the output directory.")
            return

        # Search for video files in the input directory.
        video_files = []
        for file in os.listdir(self.input_dir.get()):
            if file.lower().endswith((".mp4", ".mov", ".avi")):
                video_files.append(os.path.join(self.input_dir.get(), file))
        if not video_files:
            messagebox.showerror("Error", "No video files were found in the selected directory.")
            return

        # Configure progress based on the number of discovered files
        self.total_files = len(video_files)
        self.processed_files = 0
        self.progress.config(maximum=self.total_files, value=0)

        # Clear the verbose output area.
        self.verbose_text.delete(1.0, "end")

        # Get output format and camera type
        selected_format = self.out_format_var.get()  # "GPX", "CSV", or "KML"
        selected_camera = self.camera_var.get()        # "GoPRO Hero 10 or earlier" or "GoPRO Hero 11 or 13"

        # Process each video in its own thread
        for video_file in video_files:
            base_name = os.path.splitext(os.path.basename(video_file))[0]
            output_file = os.path.join(self.output_dir.get(), base_name)
            args = argparse.Namespace()
            args.verbose = self.verbose_var.get()
            args.binary = self.binary_var.get()
            args.skip = self.skip_var.get()
            args.skip_dop = self.skip_dop_var.get()
            args.dop_limit = self.dop_limit_var.get()
            # Configure output based on the selected format
            if selected_format == "GPX":
                args.gpx = True; args.kml = False; args.csv = False
            elif selected_format == "CSV":
                args.gpx = False; args.kml = False; args.csv = True
            elif selected_format == "KML":
                args.gpx = False; args.kml = True; args.csv = False
            args.files = [video_file]
            args.outputfile = output_file
            # Set the gui attribute and the camera type
            args.gui = True
            args.camera = selected_camera

            # Start processing in a separate thread
            threading.Thread(target=self.run_processing, args=(args, selected_format)).start()
            time.sleep(0.1)  # Optional short pause

    def run_processing(self, args, selected_format):
        try:
            # Save original descriptors
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            old_exit = sys.exit

            # In GUI mode, override sys.exit to avoid unexpected closures
            sys.exit = lambda code=0: None

            # If Verbose mode is enabled, redirect output to the Text widget
            if self.verbose_var.get():
                sys.stdout = TextRedirector(self.verbose_text)
                sys.stderr = TextRedirector(self.verbose_text)

            # Call the main processing function
            main_core(args)

            # Post-processing based on camera type and format
            if args.camera == "GoPRO Hero 11 or 13":
                if selected_format == "CSV":
                    self.post_process_csv(args.outputfile + ".csv")
                elif selected_format == "GPX":
                    self.post_process_gpx(args.outputfile + ".gpx")
                elif selected_format == "KML":
                    self.post_process_kml(args.outputfile + ".kml")
        except SystemExit:
            pass
        except Exception as e:
            # Internal error handling or logging
            messagebox.showerror("Error", f"An error occurred: {e}")
        finally:
            # Restore stdout, stderr, and sys.exit
            sys.exit = old_exit
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            # Increment the processed files counter and update the progress bar
            self.increment_progress()

    def post_process_csv(self, csv_path):
        # Implement additional processing for CSV if necessary
        pass

    def post_process_gpx(self, gpx_path):
        # Implement additional processing for GPX if necessary
        pass

    def post_process_kml(self, kml_path):
        # Implement additional processing for KML if necessary
        pass

    def increment_progress(self):
        self.processed_files += 1
        self.progress["value"] = self.processed_files
        if self.processed_files >= self.total_files:
            # All files have been processed, start completion animation
            self.after(100, self.complete_progress)

    def complete_progress(self):
        current_value = self.progress["value"]
        maximum = self.progress["maximum"]
        if current_value < maximum:
            self.progress["value"] = current_value + 1
            self.after(50, self.complete_progress)
        else:
            # Once complete, show completion notification
            messagebox.showinfo("Process Completed", "File processing has successfully finished.")

if __name__ == "__main__":
    old_exit = sys.exit
    sys.exit = lambda code=0: None
    try:
        app = GoPro2GPXGUI()
        app.mainloop()
    except Exception as e:
        print(f"Critical error in the application: {e}")
    finally:
        sys.exit = old_exit