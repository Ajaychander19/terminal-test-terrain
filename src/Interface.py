import tkinter
from tkinter import filedialog
from messages import *
from PhoneId import *
from traceMap import *
from converfile import *
from constantPath import *
import sys
import re
import webbrowser
from tkinter import font
from tkinter import messagebox, Canvas, BOTH

import xcalyzer
import cartoradio


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
                              font=("Arial", "10", "normal"), wraplengt=200)
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
            self.working_directory = r"c:\users"
        else:
            self.working_directory = r"./"

        self.lnameLabel = tkinter.Label(self, text="COVERAGE OF 4G BASE STATIONS", font=boldFont,
                                        background='light blue')
        self.lnameLabel.pack(padx=5, pady=5)

        self.defaultPath = tkinter.Button(self, command=lambda: self.button_click(1), text="Configuration",
                                          font=boldFont, background='light green')
        self.defaultPath.configure(height=3, width=25)
        self.defaultPath.pack(padx=5, pady=5)

        self.pcap_conversion = tkinter.Button(self, command=lambda: self.button_click(2),
                                              text="Field-test *.csv to *.pcap \n and *.json conversion",
                                              font=boldFont, background='light green')
        self.pcap_conversion.configure(height=3, width=25)
        self.pcap_conversion.pack(padx=5, pady=5)
        self.pcap_conversion_ttp = CreateToolTip(self.pcap_conversion,
                                                 "Choosing the Field-test file from the ZkSamp for generating "
                                                 "Field-test "
                                                 "json files as well as the pcap files corresponde to operators")

        self.cartoradio_files = tkinter.Button(self, command=lambda: self.button_click(3),
                                               text="Cartoradio File Conversion", font=boldFont,
                                               background='light green')
        self.cartoradio_files.configure(height=3, width=25)
        self.cartoradio_files.pack(padx=5, pady=5)
        self.cartoradio_files_ttp = CreateToolTip(
            self.cartoradio_files,
            "Choosing two csv files from the cartoradio for generating a new csv file with all the information needed ")

        self.association = tkinter.Button(self, command=lambda: self.button_click(4),
                                          text="Cell Association Processing", font=boldFont, background='light green')
        self.association.configure(height=3, width=25)
        self.association.pack(padx=5, pady=5)
        self.association_ttp = CreateToolTip(
            self.association,
            "Choose the .csv site file created from the 'Cartoradio File Conversion' and the json field-test files")

        self.visualizaion = tkinter.Button(self, command=lambda: self.button_click(5),
                                           text="Visualisation", font=boldFont, background='light green')
        self.visualizaion.configure(height=3, width=25)
        self.visualizaion.pack(padx=5, pady=5)

        self.canvas = Canvas(self, height=20)
        self.canvas.pack()
        self.color = 'green'
        self.rec = self.canvas.create_rectangle(10000, 20, 20, 2,
                                                outline="#fb0", fill=self.color)

    def change_color(self, color):
        self.canvas.itemconfig(self.rec, fill=color)

    def button_click(self, number):
        """ handle button click event and output text from entry area"""
        if number == 1:  # Selecting output directory.

            self.change_color('red')
            self.working_directory = filedialog.askdirectory()
            self.change_color('green')

        elif number == 2:  # Field-testing trace file.

            self.change_color('red')
            files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose a file')

            if len(files) != 0:
                # csvtoPcap(files,self.working_directory)

                for f in files:
                    conv = xcalyzer.XcalConverter(f)
                    conv.process(self.working_directory)

                # Removing temporary files.
                filelist = [f for f in os.listdir(getPathText(""))]
                for f in filelist:
                    os.remove(os.path.join(getPathText(""), f))

            else:
                messagebox.showinfo("Warning", "Select at least one file")

            self.change_color('green')

        elif number == 3:  # Cartoradio conversion, producing site and zone files.

            self.change_color('red')
            files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose a file')
            if len(files) < 2:
                messagebox.showinfo("Warning", "Two files are expected.")
            else:
                # createSite_json(files,self.working_directory)
                site_file = files[0] if 'Sites' in files[0] else files[1]
                ant_file = files[0] if 'Antennes' in files[0] else files[1]

                cartoradio.process_cartoradio(site_file, ant_file, self.working_directory)

            self.change_color('green')

        elif number == 4:  # association
            self.change_color('red')
            files = filedialog.askopenfilenames(initialdir=self.working_directory, title='Choose a file')
            if len(files) >= 2:
                cell = Associate_cell(files, self.working_directory)
                if cell == "ERROR":
                    messagebox.showinfo("Warning", "There are not enough files ")
                print("done association")
            else:
                messagebox.showinfo("Warning", "There are not enough files ")
            self.change_color('green')
        else:
            self.change_color('red')
            #            url = "http://localhost:9090/index.html"
            url = "file://" + getLeaflet('index.html')
            # url="file:///"+os.path.abspath("..\\..\\leaflet\\index.html")
            try:
                print("try to open url", url, " with default browser")
                webbrowser.open_new_tab(url)
                localhost()
            except webbrowser.Error:
                print("Something went wrong when opening webbrowser")

            self.change_color('green')

        pass


# Entry point.
if __name__ == "__main__":
    root = tkinter.Tk()
    guiFrame = GUI(root)
    root.title("4G network")
    guiFrame.configure(background="gray")
    guiFrame.mainloop()
