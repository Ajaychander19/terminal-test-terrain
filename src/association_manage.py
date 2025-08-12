import os, time
from collections import defaultdict
import tkinter as tk
from tkinter import ttk, messagebox

# UI to resolve conflict 
class ConflictDialog(tk.Toplevel):
    """
        Displays, for a PCI-EARFCN pair, the different associations found
        on the CEVCAA side and the merged ASSOC side. The user selects:
        - keep the one from the cevcaa
        - replace with one from the merger
        - 'none' (delete the association from cevcaa)
        - add (if the new association does not exist in cevcaa)
        Return: decision dictionary.
    """

    # Constructor of the dialog
    def __init__(self, parent, pci, earfcn, cevcaa_list, merged_list, mode="conflict"):
        super().__init__(parent)
        self.title(f"PCI {pci} – EARFCN {earfcn}")
        self.resizable(False, False) # Disable resizing
        self.result = None # Result of the dialog

        info = ttk.Label(self, text=f"PCI={pci}  EARFCN={earfcn}", font=("TkDefaultFont", 11, "bold")) # Title of the dialog
        info.pack(padx=12, pady=(12,6)) # Dimensions of the 'info' vertically and horizontally

        frame = ttk.Frame(self) # Vertical container for the lists
        frame.pack(padx=12, pady=6, fill="x") # Dimensions of the 'frame' vertically and horizontally, fills the x-axis

        # Formatted lists
        def fmt(r):
            return f"Site {r['Cartoradio_Number']}  Ant {r['Ant_Number']}  Score={r['Score']:.4f}"

        # Left side: cevcaa associations
        ttk.Label(frame, text="cevcaa:").grid(row=0, column=0, sticky="w") # sticky="w" aligns the label to the left
        cevcaa_box = tk.Listbox(frame, height=min(6, max(1,len(cevcaa_list))), width=60) 
        for r in cevcaa_list: 
            cevcaa_box.insert(tk.END, fmt(r)) # Insert formatted lines of cevcaa in the listbox
        cevcaa_box.grid(row=1, column=0, padx=(0,10)) # Listbox on the second row, first column

        # Right side: merged associations
        ttk.Label(frame, text="Meged association:").grid(row=0, column=1, sticky="w") 
        merged_box = tk.Listbox(frame, height=min(6, max(1,len(merged_list))), width=60)
        for r in merged_list: 
            merged_box.insert(tk.END, fmt(r)) # Insert formatted lines of merged in the listbox
        merged_box.grid(row=1, column=1) # Listbox on the second row, second column

        # Separator between the two lists
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=12, pady=6) # fill="x" to fill the entire width of the dialog

        self.choice = tk.StringVar() # Variable to store the choice of the user

        # Construct radio buttons for choices
        choices = []
        if mode == "conflict":
            self.choice.set("keep_cevcaa") # Default choice is to keep cevcaa
            choices.append(("Keep values of cevcaa", "keep_cevcaa"))
            for i, r in enumerate(merged_list):
                choices.append((f"Replace with value {i+1} of assoc file: {fmt(r)}", f"use_assoc_{i}"))
            choices.append(("Delete association from cevcaa", "none"))
        elif mode == "new":
            self.choice.set("skip") # Default choice is to skip
            for i, r in enumerate(merged_list):
                choices.append((f"Add: {fmt(r)}", f"add_assoc_{i}"))
            choices.append(("Don't add", "skip"))

        # Create radio buttons for each choice
        for txt, val in choices:
            ttk.Radiobutton(self, text=txt, value=val, variable=self.choice).pack(anchor="w", padx=12) # anchor="w" aligns the radio buttons to the left

        # Buttons validation
        btns = ttk.Frame(self)
        btns.pack(pady=10)
        ttk.Button(btns, text="OK", command=self._ok).pack(side="left", padx=6)
        ttk.Button(btns, text="Cancel", command=self._cancel).pack(side="left", padx=6)
        
        self.grab_set() # Prevent interaction with other windows
        self.wait_visibility() # Wait for the dialog to be visible
        self.focus() # Set focus on the dialog to receive keyboard events

    # Method to handle the OK button click
    def _ok(self):
        self.result = self.choice.get()
        self.destroy()

    # Method to handle the Cancel button click
    def _cancel(self):
        self.result = None
        self.destroy()


ASSOC_HEADER = ["ASSOC","Cartoradio_Number","Ant_Number","TAC","CID","EARFCN","PCI","Score"]

# Function to read file and return dict with useful data for later 
def _read_assoc_file(path, require_version=True, min_version=3.0):
    rows = []
    boolean_version = False

    # Open file and iterates through all lines of the file
    with open(path, newline='', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip() # delete leading and trailing whitespace
            if not line:
                continue

            # Check if it the right version of file
            if line.upper().startswith("VERSION|"):
                after = line.split("|", 1)[1].strip() # get the version number after "VERSION|"
                try:
                    v = float(after)
                    boolean_version = True
                    if v < float(min_version):
                        raise RuntimeError(
                            f"error: this file is not compatible with this program version (VERSION<{min_version})."
                        )
                except ValueError:
                    pass
                continue

            # Ignore lines that are not part of the ASSOC section
            if not line.startswith("ASSOC|"):
                continue

            parts = line.split('|')
            if len(parts) < 8:
                continue # Invalid line, not enough parts

            # Ignore header
            if parts[1].strip().lower() == "cartoradio_number":
                continue

            # EARFCN/PCI must be integers, Score must be float
            try:
                earfcn = parts[5].strip()
                pci    = parts[6].strip()
                score  = float(parts[7].strip())
                int(earfcn); int(pci)
            except ValueError:
                continue

            # Build a row dict 
            rows.append({
                "Cartoradio_Number": parts[1].strip(),
                "Ant_Number":        parts[2].strip(),
                "TAC":               parts[3].strip(),
                "CID":               parts[4].strip(),
                "EARFCN":            earfcn,
                "PCI":               pci,
                "Score":             score,
                "_source":           os.path.basename(path), # save path name for later 
            })

    # If a numeric VERSION is required and none was found, fail with a message
    if require_version and not boolean_version:
        raise RuntimeError("error: this file has no numeric VERSION line; please use a newer version of the program.")

    return rows

def _read_cevcaa(path):
    """ Reads the ASSOC section of a cevcaa without requiring a version. """
    return _read_assoc_file(path, require_version=False)

def _write_cevcaa_with_assoc(assoc_rows, path_out):
    """
        Rewrites a cevcaa, adds the header then the new ASSOC lines at the end of the file.
    """
    with open(path_out, "w", newline='', encoding='utf-8') as f:

        # Add header
        f.write("|".join(ASSOC_HEADER) + "\n")

        # Add all ASSOC lines
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
    """
        Merge some assoc*.csv:
        - For the same association (EARFCN, PCI, Carto, Ant): score = product of scores
        - otherwise we keep all the recordings.
    """
    bucket = defaultdict(list) # key: (EARFCN, PCI, Carto, Ant) -> list of row dicts coming from all files
    for p in paths:
        for r in _read_assoc_file(p):
            key = (r["EARFCN"], r["PCI"], r["Cartoradio_Number"], r["Ant_Number"]) # Create a key for the bucket
            bucket[key].append(r) # Append the row to the list in the bucket, grouping by the key

    merged = []
    for key, lst in bucket.items():
        # Product of scores
        score = 1.0
        for r in lst:
            score *= float(r["Score"])

        EARFCN, PCI, Carto, Ant = key

        # Build the merged row
        # _source is a concatenation of all sources to keep track of where the data comes
        merged.append({
            "Cartoradio_Number": Carto,
            "Ant_Number": Ant,
            "TAC": r["TAC"],
            "CID": r["CID"],
            "EARFCN": EARFCN,
            "PCI": PCI,
            "Score": score,
            "_source": "+".join(sorted(set(r["_source"] for r in lst)))
        })
    return merged

def _index_by_pci_earfcn(rows):
    """ Group lines by couple -> useful to compare cevcaa and merged assoc files """
    grp = defaultdict(list)
    for r in rows:
        grp[(r["PCI"], r["EARFCN"])].append(r)
    return grp

def _same_assoc_key(r):
    """ Return group with same assoc """
    return (r["EARFCN"], r["PCI"], r["Cartoradio_Number"], r["Ant_Number"])


def manage_cevcaa(cevcaa_file, assoc_files, working_dir, parent=None):
    """
        All the process:
        - load cevcaa ASSOC rows and merged ASSOC from assoc_files
        - multiply scores for identical associations
        - if same (PCI, EARFCN) has different sites/antennas -> open a ConflictDialog to decide
        - if a (PCI, EARFCN) exists only in merged -> offer to add it (mode='new')
        - sort and write the final cevcaa-out file + show a small summary
    """
    # Load data
    cevcaa_rows = _read_cevcaa(cevcaa_file)
    merged_rows = _merge_assoc_files(assoc_files)

    # Index
    idx_cevcaa = _index_by_pci_earfcn(cevcaa_rows)
    idx_merged = _index_by_pci_earfcn(merged_rows)

    # Work on a dict keyed by 'same assoc key' to make replace/remove/add easy
    cevcaa_by_key = { _same_assoc_key(r): dict(r) for r in cevcaa_rows }

    # Union of all (PCI, EARFCN) couples present in either cevcaa or merged
    all_keys = set(idx_cevcaa.keys()) | set(idx_merged.keys())


    for (pci, earfcn) in sorted(all_keys, key=lambda x: (int(x[0]), int(x[1])) if x[0].isdigit() and x[1].isdigit() else x): # sort by PCI, EARFCN in ascending order
        
        # Get the lists of associations for this PCI-EARFCN pair
        list_c = idx_cevcaa.get((pci, earfcn), [])
        list_m = idx_merged.get((pci, earfcn), [])

        if list_c and list_m:
            # for each assoc cevcaa, see if exists an identical in merged 
            identical_pairs = []
            for rc in list_c:
                for rm in list_m:
                    if _same_assoc_key(rc) == _same_assoc_key(rm):
                        identical_pairs.append((rc, rm))

            # if identical then calculate score with product of each of them
            for rc, rm in identical_pairs:
                k = _same_assoc_key(rc)
                new_score = float(rc["Score"]) * float(rm["Score"])
                cevcaa_by_key[k]["Score"] = new_score

            # if same couple without same antenna then open a dialog
            c_sites = {(r["Cartoradio_Number"], r["Ant_Number"]) for r in list_c}
            m_sites = {(r["Cartoradio_Number"], r["Ant_Number"]) for r in list_m}
            if c_sites != m_sites:
            # "conflict" case
                dlg = ConflictDialog(parent or tk._get_default_root(), pci, earfcn, list_c, list_m, mode="conflict") # Create ConflictDialog if parent is None, otherwise use the parent window
                dlg.wait_window()  # <= IMPORTANT: wait closing of dialog
                
                # user cancelled -> no change
                if dlg.result is None:
                    pass

                # keep current cevcaa associations (identical already updated)
                elif dlg.result == "keep_cevcaa":
                    pass

                # remove association from cevcaa
                elif dlg.result == "none":
                    for rc in list_c:
                        cevcaa_by_key.pop(_same_assoc_key(rc), None) # delete cevcaa association

                # replace with one from merged
                elif dlg.result.startswith("use_assoc_"):
                    i = int(dlg.result.split("_")[-1]) # get index of merged association, -1 to get the last part of the string
                    chosen = list_m[i]
                    for rc in list_c:
                        cevcaa_by_key.pop(_same_assoc_key(rc), None)
                    cevcaa_by_key[_same_assoc_key(chosen)] = dict(chosen) # add the chosen merged association to cevcaa


        elif list_m and not list_c:
            # new association detected in merged
            # "new asso" case
            dlg = ConflictDialog(parent or tk._get_default_root(), pci, earfcn, [], list_m, mode="new")
            dlg.wait_window()  # <= IIMPORTANT: wait closing of dialog
            if dlg.result is None or dlg.result == "skip":
                pass
            elif dlg.result.startswith("add_assoc_"):
                i = int(dlg.result.split("_")[-1])
                chosen = list_m[i]
                cevcaa_by_key[_same_assoc_key(chosen)] = dict(chosen)

    # Produce the new ordered list and write the file
    final_rows = list(cevcaa_by_key.values()) 
    final_rows.sort(key=lambda r: (int(r["EARFCN"]), int(r["PCI"]),
                                   r["Cartoradio_Number"], r["Ant_Number"]) if r["EARFCN"].isdigit() and r["PCI"].isdigit() else
                                  (r["EARFCN"], r["PCI"], r["Cartoradio_Number"], r["Ant_Number"])) # Sort by EARFCN, PCI, Cartoradio_Number, Ant_Number in ascending order
    
    base = os.path.splitext(os.path.basename(cevcaa_file))[0] # Take base name of cevcaa file without extension
    ts = time.strftime("%Y%m%d_%H%M%S") # Timestamp for output file
    out_path = os.path.join(working_dir, f"{base}_updated_{ts}.csv") # Output file path with timestamp and cevcaa base name
    _write_cevcaa_with_assoc(final_rows, out_path)

    # Print summary in terminal
    msg = (f"Input cevcaa: {os.path.basename(cevcaa_file)}\n"
           f"Assoc merged: {len(merged_rows)} lines (after merged by site/antena identical)\n"
           f"Output: {os.path.basename(out_path)}\n"
           f"Total ASSOC written: {len(final_rows)}")
    print(msg)
    if parent:
        try:
            messagebox.showinfo("Summary", msg, parent=parent)
        except:
            messagebox.showinfo("Summary", msg)
