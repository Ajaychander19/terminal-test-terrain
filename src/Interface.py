import sys
import os
import platform
import time
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox

# Import Pillow for image handling
try:
    from PIL import Image, ImageTk
except ImportError:
    # In a real environment, run: pip install Pillow
    Image = None
    ImageTk = None

# Try to import customtkinter for a modern look
try:
    import customtkinter as ctk
except ImportError:
    ctk = None

# Existing imports from the original script
try:
    from constantPath import *
    import xcalyzer
    import cartoradio
    import association
    from viavianalyzer import Viavilyzer
    import gmonyzer
    from association_manage import manage_cevaf
    
    # Add path to COMET source dir
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../COMET/src')))
    from shared.CometToCevConverter import CometToCevConverter
except ImportError:
    pass

class ModernGUI(ctk.CTk if ctk else tk.Tk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("4G/5G Network Coverage Analyzer")
        self.geometry("900x800") # Increased height to accommodate logos
        
        if ctk:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
        
        self.working_directory = r"../donnees"
        
        # Layout configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar Frame
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0) if ctk else tk.Frame(self)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="4G/5G COVERAGE", font=ctk.CTkFont(size=20, weight="bold")) if ctk else tk.Label(self.sidebar_frame, text="4G/5G COVERAGE")
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.dir_button = ctk.CTkButton(self.sidebar_frame, text="Select Data Directory", command=lambda: self.button_click(1)) if ctk else tk.Button(self.sidebar_frame, text="Select Data Directory", command=lambda: self.button_click(1))
        self.dir_button.grid(row=1, column=0, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="Status: Ready", text_color="green") if ctk else tk.Label(self.sidebar_frame, text="Status: Ready")
        self.status_label.grid(row=2, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w") if ctk else None
        if ctk:
            self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
            self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                command=self.change_appearance_mode_event)
            self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
            self.appearance_mode_optionemenu.set("Dark")

        # Main Content Frame
        self.main_frame = ctk.CTkScrollableFrame(self, label_text="Processing Tools") if ctk else tk.Frame(self)
        self.main_frame.grid(row=0, column=1, padx=(20, 20), pady=(20, 20), sticky="nsew")
        
        # --- LOGOS SECTION ---
        self.setup_logos()
        
        # Tool Sections
        self.create_tool_section("Data Conversion", [
            ("Viavi *.csv conversion", 5, "Convert Viavi CSV files to measurement files."),
            ("Aof file processing (Xcal)", 2, "Process Accuver Xcal files for association."),
            ("GMon Pro file Processing", 9, "Convert GMon Pro measurements to CSV."),
            ("COMET conversion", 8, "Convert COMET measurements to CEV format."),
            ("Cartoradio conversion", 3, "Convert Cartoradio site and antenna files.")
        ], 0)

        self.create_tool_section("Association & Analysis", [
            ("Cell Association Processing", 4, "Associate measurements with cell sites."),
            ("Use an Association File", 6, "Process using an existing association file."),
            ("Manage Association", 11, "Manage and merge association files.")
        ], 1)

        self.create_tool_section("Visualization", [
            ("Open Visualization", 7, "Open the interactive map in your browser.")
        ], 2)

    def setup_logos(self):
        """Helper to setup the 4 logos at the top of main_frame"""
        if not Image or not ImageTk:
            return

        # Configuration for the 4 logos: (filename, width, height)
        logo_configs = [
            ("logo1.jpeg", 100, 60),
            ("logo2.jpeg", 60, 60),
            ("logo3.jpeg", 100, 60),
            ("logo4.jpeg", 100, 60)
        ]

        # Container for logos
        logos_container = ctk.CTkFrame(self.main_frame, fg_color="transparent") if ctk else tk.Frame(self.main_frame)
        logos_container.pack(fill="x", padx=10, pady=(5, 15))
        
        # Center the logos using a sub-frame
        center_frame = ctk.CTkFrame(logos_container, fg_color="transparent") if ctk else tk.Frame(logos_container)
        center_frame.pack(expand=True)

        self.logo_images = [] # Keep references to prevent garbage collection

        base_path = os.path.join(os.path.dirname(__file__), '..', 'logos')

        for i, (filename, w, h) in enumerate(logo_configs):
            path = os.path.join(base_path, filename)
            if os.path.exists(path):
                try:
                    img = Image.open(path)
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    self.logo_images.append(photo)
                    
                    lbl = ctk.CTkLabel(center_frame, image=photo, text="") if ctk else tk.Label(center_frame, image=photo)
                    lbl.pack(side="left", padx=15)
                except Exception as e:
                    print(f"Error loading logo {filename}: {e}")
            else:
                # Placeholder if file doesn't exist
                lbl = ctk.CTkLabel(center_frame, text=f"[{filename}]", font=("Arial", 10)) if ctk else tk.Label(center_frame, text=filename)
                lbl.pack(side="left", padx=15)

    def create_tool_section(self, title, buttons, row_idx):
        section_frame = ctk.CTkFrame(self.main_frame) if ctk else tk.Frame(self.main_frame)
        section_frame.pack(fill="x", padx=10, pady=10)
        
        label = ctk.CTkLabel(section_frame, text=title, font=ctk.CTkFont(size=16, weight="bold")) if ctk else tk.Label(section_frame, text=title)
        label.pack(anchor="w", padx=10, pady=5)

        for btn_text, btn_num, tooltip in buttons:
            btn_container = ctk.CTkFrame(section_frame, fg_color="transparent") if ctk else tk.Frame(section_frame)
            btn_container.pack(fill="x", padx=20, pady=2)
            
            btn = ctk.CTkButton(btn_container, text=btn_text, width=250, command=lambda n=btn_num: self.button_click(n)) if ctk else tk.Button(btn_container, text=btn_text, command=lambda n=btn_num: self.button_click(n))
            btn.pack(side="left", pady=5)
            
            info_label = ctk.CTkLabel(btn_container, text=f"  ℹ️ {tooltip}", font=ctk.CTkFont(size=11), text_color="gray") if ctk else tk.Label(btn_container, text=tooltip)
            info_label.pack(side="left", padx=10)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def set_busy(self, is_busy):
        if is_busy:
            self.status_label.configure(text="Status: Processing...", text_color="orange")
            self.update_idletasks()
        else:
            self.status_label.configure(text="Status: Ready", text_color="green")

    def button_click(self, number):
        self.set_busy(True)
        try:
            if number == 1:  # Selecting output directory
                dir_path = filedialog.askdirectory(title="Select data directory", initialdir=self.working_directory)
                if dir_path:
                    self.working_directory = dir_path
                    messagebox.showinfo("Directory Updated", f"Working directory set to:\n{dir_path}")

            elif number == 2:  # Xcal
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose Xcal files',
                                                    filetypes=(("AOF file", "*.aof"), ("all files", "*.*")))
                if files:
                    if len(files) > 1:
                        XcalMerged = xcalyzer.XcalMerger()
                        f = XcalMerged.merge(self.working_directory, files)
                        xcalyzer.XcalConverter(f).process_nopcap(self.working_directory)
                    else:
                        for f in files:
                            xcalyzer.XcalConverter(f).process(self.working_directory)
                    messagebox.showinfo("Success", "Xcal processing completed.")

            elif number == 3:  # Cartoradio
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose Cartoradio files',
                                                    filetypes=[("Cartoradio files", ("Antennes_Emetteurs_Bandes_Cartoradio*.csv", "Sites_Cartoradio*.csv")),
                                                            ("All files", "*.*")])
                if len(files) == 2:
                    site_file = files[0] if 'Sites' in files[0] else files[1]
                    ant_file = files[0] if 'Antennes' in files[0] else files[1]
                    cartoradio.process_cartoradio(site_file, ant_file, self.working_directory, 'LTE')
                    cartoradio.process_cartoradio(site_file, ant_file, self.working_directory, '5G')
                    messagebox.showinfo("Success", "Cartoradio conversion completed.")
                elif files:
                    messagebox.showerror("Error", "Two files expected (Sites and Antennes).")

            elif number == 4:  # Association
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose measurement and site files',
                                                    filetypes=(("CSV file", "*.csv"), ("all files", "*.*")))
                if len(files) == 2:
                    site_file = files[0] if 'sites' in files[0] else files[1]
                    meas_file = files[1] if 'sites' in files[0] else files[0]
                    association.CellAssociator(meas_file, site_file, self.working_directory).process_asso()
                    messagebox.showinfo("Success", "Association processing completed.")
                elif files:
                    messagebox.showerror("Error", "Two files expected.")

            elif number == 5:  # Viavi
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose Viavi files',
                                                    filetypes=(("CSV file", "*.csv"), ("all files", "*.*")))
                if files:
                    for f in files:
                        Viavilyzer.produces_csv_op_files(f, self.working_directory)
                    messagebox.showinfo("Success", "Viavi conversion completed.")

            elif number == 6:  # Use existing association
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose meas, site, and assoc files',
                                                    filetypes=(("CSV file", "*.csv"), ("all files", "*.*")))
                if len(files) == 3:
                    # Logic to identify files (simplified from original)
                    site_file = next((f for f in files if 'sites' in f), None)
                    assoc_file = next((f for f in files if 'caf' in f), None)
                    meas_file = next((f for f in files if f != site_file and f != assoc_file), None)
                    
                    if site_file and assoc_file and meas_file:
                        association.CellAssociator(meas_file, site_file, self.working_directory).calculate_association(0, assoc_file)
                        messagebox.showinfo("Success", "Association calculation completed.")
                    else:
                        messagebox.showerror("Error", "Could not identify files correctly.")
                elif files:
                    messagebox.showerror("Error", "Three files expected.")

            elif number == 7:  # Visualization
                url = "file://" + getLeaflet('index.html')
                webbrowser.open_new_tab(url)

            elif number == 8:  # COMET
                file_path = filedialog.askopenfilename(initialdir=self.working_directory, title='Choose COMET file',
                                                       filetypes=(("CSV file", "*.csv"), ("all files", "*.*")))
                if file_path:
                    with CometToCevConverter(file_path, output_dir=self.working_directory, create_date_dir=False) as converter:
                        converter.process()
                    messagebox.showinfo("Success", "COMET conversion completed.")

            elif number == 9:  # GMon Pro
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose GMon Pro files')
                if files:
                    if len(files) > 1:
                        merged = gmonyzer.GMonProMerger().merge(self.working_directory, files)
                        gmonyzer.GMonProConverter(merged, self.working_directory).process()
                    else:
                        gmonyzer.GMonProConverter(files[0], self.working_directory).process()
                    messagebox.showinfo("Success", "GMon Pro processing completed.")

            elif number == 11:  # Manage Association
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose cevcaf and assoc files')
                if files:
                    cevaf_paths = [p for p in files if 'cevaf' in os.path.basename(p).lower() or 'cevcaf' in os.path.basename(p).lower()]
                    assoc_paths = [p for p in files if 'assoc' in os.path.basename(p).lower()]
                    cevaf_file = cevaf_paths[0] if cevaf_paths else None
                    manage_cevaf(cevaf_file, assoc_paths, self.working_directory, parent=self)
                    messagebox.showinfo("Success", "Association management completed.")

        except Exception as e:
            messagebox.showerror("Runtime Error", f"An error occurred:\n{str(e)}")
        finally:
            self.set_busy(False)

if __name__ == "__main__":
    app = ModernGUI()
    app.mainloop()
