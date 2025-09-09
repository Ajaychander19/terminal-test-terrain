import sys
import tkinter
from tkinter import filedialog

from constantPath import *

import webbrowser
from tkinter import font
from tkinter import messagebox, Canvas

import xcalyzer
import cartoradio
import association
from viavianalyzer import Viavilyzer
import gmonyzer
from association_manage import manage_cevcaa
import time

# Add path to COMET source dir to be able to find its modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../COMET/src')))
from shared.CometToCevConverter import CometToCevConverter


class CreateToolTip(object):
    """Creates a tooltip for a given widget."""

    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)
        self.tw = None

    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tkinter.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tkinter.Label(self.tw, text=self.text, justify='left',
                              background='yellow', relief='solid', borderwidth=1,
                              font=("Arial", "10", "normal"), wraplength=200)
        # label.config(width=200)
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()


class GUI(tkinter.Frame):
    """TKInter main window frame"""

    def __init__(self, master=None, **kwargs):
        tkinter.Frame.__init__(self, master, width=768, height=576, borderwidth=1, **kwargs)
        self.pack()
        boldFont = font.Font(size=14, weight="bold", family='Arial')
        if platform.system() == "Windows":
            self.working_directory = r"../donnees"
        else:
            self.working_directory = r"../donnees"

        self.lnameLabel = tkinter.Label(self, text="COVERAGE OF 4G BASE STATIONS", font=boldFont,
                                        background='light blue')
        self.lnameLabel.pack(padx=5, pady=5)

        self.defaultPath = tkinter.Button(self, command=lambda: self.button_click(1), text="Select data directory",
                                          font=boldFont, background='light green')
        self.defaultPath.configure(height=2, width=25)
        self.defaultPath.pack(padx=5, pady=5)

        self.viavi_conversion = tkinter.Button(self, command=lambda: self.button_click(5),
                                               text="viavi *.csv conversion",
                                               font=boldFont, background='light green')
        self.viavi_conversion.configure(height=2, width=25)
        self.viavi_conversion.pack(padx=5, pady=5)

        self.pcap_conversion = tkinter.Button(self, command=lambda: self.button_click(2),
                                              text="Aof file processing (Xcal)",
                                              font=boldFont, background='light green')

        self.pcap_conversion.configure(height=2, width=25)
        self.pcap_conversion.pack(padx=5, pady=5)
        self.pcap_conversion_ttp = CreateToolTip(self.pcap_conversion,
                                                 "Choose the Field-test Accuver Xcal files "
                                                 "to produce a measurement file that can be used by the Association "
                                                 " process, produce a pcap file if only 1 file is selected")
        
        self.cellgmonpro_conversion = tkinter.Button(self, command=lambda: self.button_click(9),
                                               text="GMon Pro file Processing",
                                               font=boldFont, background='light green')
        CreateToolTip(self.cellgmonpro_conversion,
                      "Choose a GMoN-Pro measurements file to convert it to a 'csv' measurement file that can be "
                      "used by the Association process")
        self.cellgmonpro_conversion.configure(height=2, width=25)
        self.cellgmonpro_conversion.pack(padx=5, pady=5)

        # Comet converter button
        self.comet_converter = tkinter.Button(self, command=lambda: self.button_click(8),
                                              text="COMET conversion", font=boldFont,
                                              background='light green')
        self.comet_converter.configure(height=2, width=25)
        self.comet_converter.pack(padx=5, pady=5)
        CreateToolTip(self.comet_converter,
                      "Choose a COMET measurements file to convert it to a 'cev' measurement file that can be "
                      "used by the Association process")

        self.cartoradio_files = tkinter.Button(self, command=lambda: self.button_click(3),
                                               text="Cartoradio conversion", font=boldFont,
                                               background='light green')
        self.cartoradio_files.configure(height=2, width=25)
        self.cartoradio_files.pack(padx=5, pady=5)
        self.cartoradio_files_ttp = CreateToolTip(
            self.cartoradio_files,
            "Convert Antennes_Emetteurs_Bandes_Cartoradio and"
            " Sites_Cartoradio.csv in one tractable site file")

        self.association = tkinter.Button(self, command=lambda: self.button_click(4),
                                          text="Cell Association Processing", font=boldFont, background='light green')
        self.association.configure(height=2, width=25)
        self.association.pack(padx=5, pady=5)
        self.association_ttp = CreateToolTip(
            self.association,
            "Choose the .csv site file created from the 'Cartoradio File Conversion' and the .csv measurement file")

        self.useassoc = tkinter.Button(self, command=lambda: self.button_click(6),
                                       text="Use an Association File", font=boldFont, background='light green')
        self.useassoc.configure(height=2, width=25)
        self.useassoc.pack(padx=5, pady=5)
        self.useassoc_ttp = CreateToolTip(
            self.useassoc,
            "Choose the caf*.csv association file and the .csv measurement file")

        self.visualizaion = tkinter.Button(self, command=lambda: self.button_click(7),
                                           text="Visualisation", font=boldFont, background='light green')
        self.visualizaion.configure(height=2, width=25)
        self.visualizaion.pack(padx=5, pady=5)

        self.association_ttp = CreateToolTip(
            self.association,
            "Choose the .csv site file created from the 'Cartoradio File Conversion' and the .csv measurement file")

        self.association = tkinter.Button(self, command=lambda: self.button_click(11),
                                          text="Manage association", font=boldFont, background='light green')
        self.association.configure(height=2, width=25)
        self.association.pack(padx=5, pady=5)
        self.association_ttp = CreateToolTip(
            self.association,
            "Choose the .csv site file created from the 'Cartoradio File Conversion' and the .csv measurement file")
        
        self.canvas = Canvas(self, height=20)
        self.canvas.pack()
        self.color = 'green'
        self.rec = self.canvas.create_rectangle(10000, 20, 20, 2,
                                                outline="#fb0", fill=self.color)
        

    def change_color(self, color):
        self.canvas.itemconfig(self.rec, fill=color)

    def button_click(self, number):
        """ handle button click event and output text from entry area"""

        try:
            if number == 1:  # Selecting output directory.

                self.change_color('red')
                self.working_directory = filedialog.askdirectory(title="Select data directory (not tmp)",
                                                                 initialdir=self.working_directory)
                self.change_color('green')
            elif number == 2:  # Field-testing trace file.

                self.change_color('red')
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose a file',
                                                    filetypes=(("AOF file", "*.aof"), ("all files", "*.*")))
                nbfiles = len(files)
                if nbfiles > 1:
                    XcalMerged = xcalyzer.XcalMerger()
                    f = XcalMerged.merge(self.working_directory, files)
                    conv = xcalyzer.XcalConverter(f)
                    conv.process_nopcap(self.working_directory)

                elif len(files) != 0:
                    # csvtoPcap(files,self.working_directory)

                    for f in files:
                        start_time = time.perf_counter()
                        conv = xcalyzer.XcalConverter(f)
                        conv.process(self.working_directory)
                        elapsed = time.perf_counter() - start_time
                        print(f"Conversion duration: {elapsed:.6f} seconds")
                        
                    # Removing temporary files.
                    filelist = [f for f in os.listdir(getPathText(""))]
                    for f in filelist:
                        os.remove(os.path.join(getPathText(""), f))

                else:
                    return

                self.change_color('green')

            elif number == 3:  # Cartoradio conversion, producing site and zone files.

                self.change_color('red')
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose a file',
                                                    filetypes=[("Cartoradio files", ("Antennes_Emetteurs_Bandes_Cartoradio*.csv", "Sites_Cartoradio*.csv")),
                                                            ("All files", "*.*")])
                if len(files) == 0:
                    return
                
                elif len(files) != 2:
                    messagebox.showerror("Error", "Two files expected.")
                else:
                    # createSite_json(files,self.working_directory)
                    site_file = files[0] if 'Sites' in files[0] else files[1]
                    ant_file = files[0] if 'Antennes' in files[0] else files[1]

                    cartoradio.process_cartoradio(site_file, ant_file, self.working_directory, 'LTE')
                    cartoradio.process_cartoradio(site_file, ant_file, self.working_directory, '5G')

                self.change_color('green')

            elif number == 4:  # association

                self.change_color('red')
                files = filedialog.askopenfilenames(initialdir=self.working_directory,
                                                    title='Choose measurement file and operator sites file',
                                                    filetypes=(("cev CSV file", "cev*.csv"), ("all files", "*.*")))

                if len(files) == 0:
                    return
                
                elif len(files) != 2:
                    messagebox.showerror("Error", "Two files expected.")
                else:

                    # Associate_cell(files, self.working_directory)
                    site_file = files[0] if 'sites' in files[0] else files[1]
                    meas_file = files[1] if 'sites' in files[0] else files[0]

                    start_time = time.perf_counter()
                    association.CellAssociator(
                        meas_file,
                        site_file,
                        self.working_directory
                    ).associate_single_pass_with_ta_filter(mode=1)
                    elapsed = time.perf_counter() - start_time
                    print(f"Conversion duration: {elapsed:.6f} seconds")


                self.change_color('green')

            elif number == 5:  # viavi file processing
                self.change_color('red')
                files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose a file',
                                                    filetypes=(("CSV file", "*.csv"), ("all files", "*.*")))
                if len(files) != 0:
                    for f in files:
                        conv = Viavilyzer.produces_csv_op_files(f, self.working_directory)
                else:
                    return

                self.change_color('green')
            
            elif number == 9:  # GMon Pro measurements conversion
                self.change_color('red')

                file_paths = filedialog.askopenfilenames(
                    initialdir=self.working_directory,
                    title='Choose G-MoNPro file(s)',
                    filetypes=(("gmonpro SFR CSV file", ("gmonpro*20810*.csv")), 
                               ("gmonpro Orange CSV file", ("gmonpro*20801*.csv")),
                               ("all files", "*.*"))
                )

                nbfiles = len(file_paths)
                if nbfiles == 0:
                    return
                else:
                    try:
                        if nbfiles > 1:
                            # Merge files
                            merger = gmonyzer.GMonProMerger()
                            merged_file = merger.merge(self.working_directory, file_paths)

                            # Convert merged file
                            print(f"Merged file created: {merged_file}")
                            gmonyzer.GMonProConverter(merged_file, self.working_directory).process()

                        else:
                            # Convert single file
                            f = file_paths[0]
                            print(f"Processing file: {f}")
                            start_time = time.perf_counter()
                            gmonyzer.GMonProConverter(f, self.working_directory).process()
                            elapsed = time.perf_counter() - start_time
                            print(f"Conversion duration: {elapsed:.6f} seconds")

                    except Exception as e:
                        messagebox.showerror("Processing Error", str(e))

                self.change_color('green')


            elif number == 6:  # use an existing association
                self.change_color('red')
                files = filedialog.askopenfilenames(initialdir=self.working_directory,
                                                    title='Choose measurement file, operator sites file and association file',
                                                    filetypes=(("cev CSV file", "cev*.csv"), ("all files", "*.*")))
                if len(files) == 0:
                    return
                
                # Associate_cell(files, self.working_directory)
                elif len(files) != 3:
                    messagebox.showerror("Error", "3 files expected.")
                else:
                    if 'sites' in files[0]:
                        site_file = files[0]
                        if 'caf' in files[1]:
                            assoc_file = files[1]
                            meas_file = files[2]
                        else:
                            assoc_file = files[2]
                            meas_file = files[1]
                    elif 'sites' in files[1]:
                        site_file = files[1]
                        if 'caf' in files[0]:
                            assoc_file = files[0]
                            meas_file = files[2]
                        else:
                            assoc_file = files[2]
                            meas_file = files[0]
                    elif 'sites' in files[2]:
                        site_file = files[2]
                        if 'caf' in files[0]:
                            assoc_file = files[0]
                            meas_file = files[1]
                        else:
                            assoc_file = files[1]
                            meas_file = files[0]
                    else:
                        messagebox.showerror("Error", "No file converted from Cartoradio.")

                    association.CellAssociator(
                        meas_file,
                        site_file,
                        self.working_directory
                    ).calculate_association(0, assoc_file)
                    self.change_color('green')

            elif number == 7:
                self.change_color('red')
                url = "file://" + getLeaflet('index.html')
                try:
                    print("try to open url", url, " with default browser")
                    webbrowser.open_new_tab(url)
                except webbrowser.Error as e:
                    print("Error: {}", str(e))

                self.change_color('green')

            elif number == 8:  # Comet measurements conversion
                self.change_color('red')

                file_path = filedialog.askopenfilename(initialdir=self.working_directory, title='Choose a file',
                                                       filetypes=(("CSV file", "*.csv"), ("all files", "*.*")))
                if file_path:  # Don't display error on cancel
                    with CometToCevConverter(file_path, output_dir=self.working_directory, create_date_dir=False) as converter:
                        converter.process()

                self.change_color('green')

            elif number == 11:  # Manage cevcaa file
                self.change_color('red')
                try:
                    files = filedialog.askopenfilenames(
                        initialdir=self.working_directory,
                        title='Choose cevcaa/cevcaf and one or more assoc files',
                        filetypes=[
                            ("SFR cevcaf/assoc", ("cevcaaSFR*.csv", "cevcafSFR*.csv", "assoc_SFR*.csv")),
                            ("Orange cevcaf/assoc", ("cevcaaOrange*.csv", "cevcafOrange*.csv", "assoc_Orange*.csv")),
                            ("All files", "*.*"),
                        ]
                    )
                    if not files:
                        return

                    cevcaa_paths = [p for p in files if ('cevcaf' or 'cevcaa') in os.path.basename(p).lower()]
                    assoc_paths  = [p for p in files if 'assoc'  in os.path.basename(p).lower()]

                    if len(cevcaa_paths) > 1:
                        messagebox.showerror("Error", "You can't choose more than ONE cevcaa file.")
                        return
                    elif len(cevcaa_paths) == 1:
                        cevcaa_file = cevcaa_paths[0]
                        manage_cevcaa(cevcaa_file, assoc_paths, self.working_directory, parent=self)
                    else:
                        manage_cevcaa(None, assoc_paths, self.working_directory, parent=self)

                    messagebox.showinfo("Done", "Association management completed.")
                except Exception as e:
                    messagebox.showerror("Runtime Error", f"An error occurred:\n {e}")
                finally:
                    self.change_color('green')

        except Exception as e:
            messagebox.showerror("Runtime Error", "An error occured:\n {}".format(str(e)))


# Entry point.
if __name__ == "__main__":
    root = tkinter.Tk()
    guiFrame = GUI(root)
    root.title("4G network")
    guiFrame.configure(background="gray")
    guiFrame.mainloop()
