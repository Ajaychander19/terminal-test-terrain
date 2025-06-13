"""This module defines functions to manipulate PCAP temporary files."""

from constantPath import getPathText, getWireshark, getfileName

import subprocess

def reorder_pcap(fname: str, dest: str):
    """Reorders a given PCAP temporary file with reordercap. Produces the resulting
    PCAP temporary reordered file.

    Parameters:
        fname: the name of the temporary PCAP source file.
        dest: the name of the temporary PCAP destination file which will be created.

    Raises:
        CalledProcessError: if reordercap produces an error.
    """

    input_file = getPathText(fname)
    output_file = getPathText(dest)

    # Preparing reordercap call.
    rcap_argc = [
        getWireshark('reordercap'),     # Command path
        '-n',                           # Produce a file only if a reordering has been done.
        input_file,
        output_file
    ]

    # Calling reordercap
    subprocess.check_call(rcap_argc)


def merge_pcaps(names: list, dest: str):
    """Concatenates several given PCAP temporary files into another given PCAP temporary file with mergecap.

    Parameters:
        names: name of temporary files to concatenate.
        dest: name of the temporary output file.

    Raises:
        CalledProcessError: if mergecap produces an error.

    """
    # Preparing mergecap
    output_file = getPathText(dest)

    # Initial arguments list.
    mcap_argc = [
        getWireshark('mergecap'),
        '-a',               # Concat files.
        '-w', output_file   # File to write.
    ]

    # Adding files paths to the argument list.
    for n in names:
        mcap_argc.append(getPathText(n))

    # Calling mergecap
    subprocess.check_call(mcap_argc)


def produce_pcap(path: str, dest: str, diss_num: int):
    """Produces a PCAP file from a TXT file which contains packets data
    required in order to construct the PCAP file.

    Parameters:
        path: TXT file path.
        dest: PCAP destination file path.
        diss_num: number of the dissector to be used.
    """
    input_txt = getPathText(path)
    output_pcap = getPathText(dest)

    # Preparing text2pcap call.
    t2p_argc = [
        getWireshark('text2pcap'),  # Wireshark command path.
        '-t', '%F %H:%M:%S.%f',  # Time format to use in the pcap file.
        input_txt,  # Input .txt file.
        output_pcap,  # Output .pcap file.
        '-l', str(diss_num)  # Number of the dissector to be called.
    ]

    # Calling text2pcap
    subprocess.check_call(t2p_argc)
