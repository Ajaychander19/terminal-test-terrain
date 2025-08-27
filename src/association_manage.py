"""This module manages associations. It allows you to add associations from associations files to the cevcaa sure associations file."""

import os, time # os for file operations, time for timestamping
from collections import defaultdict # defaultdict for grouping list by keys automatically
import tkinter as tk # Tkinter for GUI elements
from tkinter import ttk, messagebox # ttk for themed widgets, messagebox for dialog boxes

ASSOC_HEADER = ["ASSOC","Cartoradio_Number","Ant_Number","TAC","CID","EARFCN","PCI","Score"]


def _fmt_assoc_row(r):
    """Formats a single association row for display."""
    return f"Site {r['Cartoradio_Number']}  Ant {r['Ant_Number']}  Score={r['Score']:.4f}"


def _join_rows_short(rows):
    """Join multiple association rows into a short string for display."""
    if not rows: 
        return "-"
    
    # Build a list of formatted items
    items = [f"{r['Cartoradio_Number']}/{r['Ant_Number']} (S={r['Score']:.3f})" for r in rows] 

    # If more than 3 items, show first 3 and indicate how many more
    if len(items) > 3:
        return ", ".join(items[:3]) + f" … (+{len(items)-3})" 
    
    # Otherwise, join all items
    return ", ".join(items)


class ScrollableTable(ttk.Frame):
    """
        A scrollable table-like frame with headings and rows of widgets.
        Use to display association conflicts and choices.
    """

    def __init__(self, parent, headings):
        """Constructor.
        headings: list of column headings (strings).
        parent: parent tk widget.
        """

        super().__init__(parent) # Call the parent constructor
        self.canvas = tk.Canvas(self, highlightthickness=0) # Canva that will hold the table
        self.scrollbar_y = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview) # Vertical scrollbar
        self.scrollbar_x = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview) # Horizontal scrollbar
        self.inner = ttk.Frame(self.canvas) # Inner frame that will contain the actual table content

        self.canvas.create_window((0,0), window=self.inner, anchor="nw") # Place the inner frame in the canvas, anchor top-left
        self.canvas.configure(yscrollcommand=self.scrollbar_y.set, xscrollcommand=self.scrollbar_x.set) # Configure canvas to update scrollbars

        self.canvas.grid(row=0, column=0, sticky="nsew") # Place canvas in grid
        self.scrollbar_y.grid(row=0, column=1, sticky="ns") # Place vertical scrollbar 
        self.scrollbar_x.grid(row=1, column=0, sticky="ew") # Place horizontal scrollbar

        # Allow the canvas to expand
        self.columnconfigure(0, weight=1) 
        self.rowconfigure(0, weight=1)

        # Create headings
        for j, h in enumerate(headings):
            lbl = ttk.Label(self.inner, text=h, font=("TkDefaultFont", 10, "bold")) # Create label for heading
            lbl.grid(row=0, column=j, sticky="w", padx=(6,12), pady=(6,4)) # Place heading label in grid, column

        # Next row index for adding new rows
        self._next_row = 1


    def add_row_widgets(self, widgets):
        """Widgets must be a list of tk widgets to add as a new row."""
        r = self._next_row
        for c, w in enumerate(widgets):
            w.grid(row=r, column=c, sticky="w", padx=(6,12), pady=4)
        self._next_row += 1

        # update scrollregion
        self.inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def bind_mousewheel(self):
        """Bind mouse wheel to scroll the canvas."""
        def _on_mousewheel(event):
            # Windows / Linux delta
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)        # Windows
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll( 1, "units"))  # Linux

class ConflictTableDialog(tk.Toplevel):
    """
        Print all the differences and new associations in a scrollable table.
        For each (PCI, EARFCN), propose an appropriate Combobox of actions (conflict vs. new).
        On validation, self.results = dict[(pci,earfcn)] -> code ('keep cevcaa','none','use_assoc_i','add_assoc_i','skip').
    """

    def __init__(self, parent, conflicts):
        """parent: parent tk widget.
        conflicts: list of tuples (pci, earfcn, list_c, list_m, mode)
        where list_c = list of cevcaa rows, list_m = list of merged rows"""
        
        super().__init__(parent) # Call parent constructor
        self.title("Resolve conflicts and new associations")
        self.geometry("1100x600") # Initial size
        self.minsize(900, 400) # Minimum size
        self.results = {}          # (pci, earfcn) -> code selected by user
        self._option_map = {}      # (pci, earfcn) -> {label -> code}
        self._vars = {}            # (pci, earfcn) -> tk.StringVar (displayed label in Combobox)

        container = ttk.Frame(self) # Main container frame
        container.pack(fill="both", expand=True, padx=10, pady=8) # Padding around

        headings = ("PCI", "EARFCN", "cevcaa (site/ant/score)", "merged (site/ant/score)", "Choice")
        self.table = ScrollableTable(container, headings)
        self.table.pack(fill="both", expand=True) # Fill available space
        self.table.bind_mousewheel() # Enable mouse wheel scrolling

        # Fill the table with conflicts/new associations
        for pci, earfcn, list_c, list_m, mode in conflicts:
            pci_s, earfcn_s = str(pci), str(earfcn) # Ensure strings
            cevcaa_txt = _join_rows_short(list_c) # Short text for cevcaa rows
            merged_txt = _join_rows_short(list_m) # Short text for merged rows

            # Construct option map and labels for Combobox
            option_map = {} # label -> code
            labels = [] # list of labels for Combobox
            if mode == "conflict":
                option_map["Keep cevcaa"] = "keep_cevcaa" # Keep existing cevcaa associations
                labels.append("Keep cevcaa") # Add to labels

                # Add options to replace by one of the merged associations
                for i, r in enumerate(list_m):
                    label = f"Replace by merged #{i+1} — {_fmt_assoc_row(r)}"
                    option_map[label] = f"use_assoc_{i}" # Code to use this merged association
                    labels.append(label)

                # Option to delete all associations for this (pci, earfcn)
                option_map["Delete association (cevcaa)"] = "none"
                labels.append("Delete association (cevcaa)") 

                # Default selection
                default_label = "Keep cevcaa"
            
            # New association case
            else: 
                for i, r in enumerate(list_m):
                    label = f"Add merged #{i+1} — {_fmt_assoc_row(r)}" # Label for adding this merged association
                    option_map[label] = f"add_assoc_{i}"
                    labels.append(label)

                option_map["Don't add"] = "skip" # Option to skip adding
                labels.append("Don't add") 
                default_label = "Don't add"

            # Store option map for this (pci, earfcn)
            self._option_map[(pci_s, earfcn_s)] = option_map

            # Create row widgets
            l_pci = ttk.Label(self.table.inner, text=pci_s)
            l_earfcn = ttk.Label(self.table.inner, text=earfcn_s)
            l_c = ttk.Label(self.table.inner, text=cevcaa_txt)
            l_m = ttk.Label(self.table.inner, text=merged_txt)

            var = tk.StringVar(value=default_label)
            self._vars[(pci_s, earfcn_s)] = var
            cb = ttk.Combobox(self.table.inner, textvariable=var, values=labels, state="readonly", width=70)

            self.table.add_row_widgets([l_pci, l_earfcn, l_c, l_m, cb])

        # Buttons frame
        btns = ttk.Frame(self)
        btns.pack(pady=8)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=self._cancel).pack(side="left", padx=6)

        self.grab_set() # Make modal
        self.wait_visibility() # Wait until window is visible
        self.focus() # Focus on this window

    def _ok(self):
        """"Collect user choices and close dialog."""
        # Translate label (in combobox) -> code interne
        for (pci, earfcn), var in self._vars.items():
            label = var.get() # Get selected label
            code = self._option_map[(pci, earfcn)].get(label) # Map to internal code
            self.results[(pci, earfcn)] = code # Store result
        self.destroy() # Close dialog

    def _cancel(self):
        """User cancelled: results = None."""
        self.results = None # Indicate cancellation
        self.destroy() # Close dialog

def _read_assoc_file(path, require_version=True, min_version=3.0):
    """Read an ASSOC file and return list of dict rows.
    If require_version is True, check that a numeric VERSION line exists and is >= min_version.
    Each dict has keys: Cartoradio_Number, Ant_Number, TAC, CID, EARFCN, PCI, Score, _source (filename).
    Invalid lines are skipped.  """

    rows = [] # List to hold valid rows
    boolean_version = False # Track if a valid VERSION line was found

    with open(path, newline='', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip() # Remove whitespace
            if not line:
                continue
            if line.upper().startswith("VERSION|"):
                after = line.split("|", 1)[1].strip() # Get text after "VERSION|"
                try:
                    v = float(after) # Try to parse as float
                    boolean_version = True # Valid version line found

                    # Check minimum version if required
                    if v < float(min_version):
                        raise RuntimeError(f"error: this file is not compatible (VERSION<{min_version}).")
                    
                except ValueError:
                    pass
                continue

            # Process only ASSOC lines
            if not line.startswith("ASSOC|"):
                continue

            parts = line.split('|') # Split line into parts

            # Ignore lines with insufficient parts
            if len(parts) < 8:
                continue
            
            # Skip header line
            if parts[1].strip().lower() == "cartoradio_number":
                continue
            
            # Parse and validate numeric fields
            try:
                earfcn = parts[5].strip()
                pci    = parts[6].strip()
                score  = float(parts[7].strip())
                int(earfcn); int(pci)
            except ValueError:
                continue

            # Add valid row to list
            rows.append({
                "Cartoradio_Number": parts[1].strip(),
                "Ant_Number":        parts[2].strip(),
                "TAC":               parts[3].strip(),
                "CID":               parts[4].strip(),
                "EARFCN":            earfcn,
                "PCI":               pci,
                "Score":             score,
                "_source":           os.path.basename(path),
            })

    # If version is required but not found, raise error
    if require_version and not boolean_version:
        raise RuntimeError("error: this file has no numeric VERSION line; please use a newer version.")
    
    # Return the list of valid rows
    return rows

def _read_cevcaa(path):
    """Read a cevcaa ASSOC file, without requiring VERSION line."""
    return _read_assoc_file(path, require_version=False)

def _write_cevcaa_with_assoc(assoc_rows, path_out):
    """Write a cevcaa ASSOC file with given assoc_rows."""

    with open(path_out, "w", newline='', encoding='utf-8') as f:
        f.write("|".join(ASSOC_HEADER) + "\n") # Write header

        # Write each association row
        for r in assoc_rows:
            row = [
                "ASSOC",
                str(r["Cartoradio_Number"]),
                str(r["Ant_Number"]),
                str(r["TAC"]),
                str(r["CID"]),
                str(r["EARFCN"]),
                str(r["PCI"]),
                f'{float(r["Score"]):.12f}'
            ]
            f.write("|".join(row) + "\n")

def _merge_assoc_files(paths):
    """Merge multiple ASSOC files by multiplying scores for identical (EARFCN, PCI, Cartoradio_Number, Ant_Number).
    Returns a list of merged assoc rows."""

    bucket = defaultdict(list) # key = (EARFCN, PCI, Cartoradio_Number, Ant_Number) -> list of rows

    # Read all files and group rows by key
    for p in paths:

        # Read each assoc file
        for r in _read_assoc_file(p):
            key = (r["EARFCN"], r["PCI"], r["Cartoradio_Number"], r["Ant_Number"]) # Grouping key
            bucket[key].append(r) # Add row to corresponding group

    merged = [] # List to hold merged rows

    # For each group, multiply scores and create merged row
    for key, lst in bucket.items():
        score = 1.0
        for r in lst:
            score *= float(r["Score"]) # Multiply scores
        EARFCN, PCI, Carto, Ant = key
        merged.append({
            "Cartoradio_Number": Carto,
            "Ant_Number": Ant,
            "TAC": lst[0]["TAC"],
            "CID": lst[0]["CID"],
            "EARFCN": EARFCN,
            "PCI": PCI,
            "Score": score,
            "_source": "+".join(sorted(set(r["_source"] for r in lst))) # Combine sources
        })
    return merged

def _index_by_pci_earfcn(rows):
    """Index a list of assoc rows by (PCI, EARFCN).
    Returns a dict: (PCI, EARFCN) -> list of rows."""
    grp = defaultdict(list) 
    for r in rows:
        grp[(r["PCI"], r["EARFCN"])].append(r)
    return grp

def _same_assoc_key(r):
    """Return a key identifying the association (EARFCN, PCI, Cartoradio_Number, Ant_Number)."""
    return (r["EARFCN"], r["PCI"], r["Cartoradio_Number"], r["Ant_Number"])

def manage_cevcaa(cevcaa_file, assoc_files, working_dir, parent=None):
    """
    Process complete for managing associations in a cevcaa file:
    - Load cevcaa and merge assoc_files
    - Multiply scores for identical associations
    - Collect conflicts and new associations
    - Open a single window to choose actions
    - Apply choices and write final file
    """

    # Load data
    cevcaa_rows = _read_cevcaa(cevcaa_file)
    merged_rows = _merge_assoc_files(assoc_files)

    # Index by (PCI, EARFCN)
    idx_cevcaa = _index_by_pci_earfcn(cevcaa_rows)
    idx_merged = _index_by_pci_earfcn(merged_rows)

    # Dict for quick access to cevcaa rows by full assoc key
    cevcaa_by_key = { _same_assoc_key(r): dict(r) for r in cevcaa_rows }

    # All (PCI, EARFCN) keys
    all_keys = set(idx_cevcaa.keys()) | set(idx_merged.keys())

    conflicts = []  # conflicts to resolve

    # Update scores and collect conflicts/new associations
    for (pci, earfcn) in sorted(
        all_keys,
        key=lambda x: (int(x[0]), int(x[1])) if x[0].isdigit() and x[1].isdigit() else x
    ):
        # Get lists of rows for this (PCI, EARFCN)
        list_c = idx_cevcaa.get((pci, earfcn), [])
        list_m = idx_merged.get((pci, earfcn), [])


        if list_c and list_m:
            # score update for identical associations
            for rc in list_c:
                for rm in list_m:
                    if _same_assoc_key(rc) == _same_assoc_key(rm):
                        k = _same_assoc_key(rc)
                        cevcaa_by_key[k]["Score"] = float(rc["Score"]) * float(rm["Score"])

            # c onflict if different sets of sites/antennas
            c_sites = {(r["Cartoradio_Number"], r["Ant_Number"]) for r in list_c}
            m_sites = {(r["Cartoradio_Number"], r["Ant_Number"]) for r in list_m}
            if c_sites != m_sites:
                conflicts.append((pci, earfcn, list_c, list_m, "conflict"))

        elif list_m and not list_c:
            # new association to consider adding
            conflicts.append((pci, earfcn, [], list_m, "new"))

    # Open dialog if there are conflicts/new associations
    if conflicts:
        dlg = ConflictTableDialog(parent or tk._get_default_root() or tk.Tk(), conflicts)
        dlg.wait_window()
        if dlg.results is None:
            # Cancelled by user
            return

        # Apply user choices
        for (pci, earfcn, list_c, list_m, mode) in conflicts:
            code = dlg.results.get((str(pci), str(earfcn)))
            if not code:
                continue

            if mode == "conflict":

                # don't change anything
                if code == "keep_cevcaa":
                    pass  

                # remove all cevcaa associations for this (pci, earfcn)
                elif code == "none":
                    for rc in list_c:
                        cevcaa_by_key.pop(_same_assoc_key(rc), None) 

                # replace by one of the merged associations
                elif code.startswith("use_assoc_"):
                    i = int(code.split("_")[-1])
                    chosen = list_m[i]
                    
                    # remove all cevcaa associations for this (pci, earfcn)
                    for rc in list_c:
                        cevcaa_by_key.pop(_same_assoc_key(rc), None)

                    # add the chosen merged association
                    cevcaa_by_key[_same_assoc_key(chosen)] = dict(chosen)

            # New association case
            elif mode == "new":
                if code.startswith("add_assoc_"):
                    i = int(code.split("_")[-1])
                    chosen = list_m[i]
                    cevcaa_by_key[_same_assoc_key(chosen)] = dict(chosen)
                # "skip" => nothing to do

    # Write final cevcaa file
    # Sort by EARFCN, PCI, Cartoradio_Number, Ant_Number
    final_rows = list(cevcaa_by_key.values())
    final_rows.sort(key=lambda r: (int(r["EARFCN"]), int(r["PCI"]),
                                   r["Cartoradio_Number"], r["Ant_Number"]) if r["EARFCN"].isdigit() and r["PCI"].isdigit()
                                   else (r["EARFCN"], r["PCI"], r["Cartoradio_Number"], r["Ant_Number"]))

    base = os.path.splitext(os.path.basename(cevcaa_file))[0]
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(working_dir, f"{base}_updated_{ts}.csv")
    _write_cevcaa_with_assoc(final_rows, out_path)

    # Summary message
    msg = (f"Input cevcaa: {os.path.basename(cevcaa_file)}\n"
           f"Assoc merged: {len(merged_rows)} lines (after merge by site/antenne identical)\n"
           f"Output: {os.path.basename(out_path)}\n"
           f"Total ASSOC written: {len(final_rows)}")
    print(msg)
    if parent:
        try:
            messagebox.showinfo("Summary", msg, parent=parent)
        except Exception:
            messagebox.showinfo("Summary", msg)
