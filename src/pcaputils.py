"""This module defines functions to manipulate PCAP temporary files."""

# Needed library : pycrate
from pycrate_asn1dir import RRCLTE

from constantPath import getPathText, getWireshark, getfileName

import binascii
import json
import subprocess


def produce_asn1(channel: str, payload: str) -> dict:
    """Produces ASN1-structured dictionary from a payload, following
    a given message type.
    
    Parameters:
        channel: message channel. Supported channels are 'BCCH:DL_SCH' and 'UL DCCH'.
        payload: hex string which contains the message binary data.

    Returns:
        ASN1-structured dictionary generated from the message.
    """
    # Extracting RRC message data.

    # Choosing message object.
    if channel == 'BCCH:DL_SCH':
        msg_obj = RRCLTE.EUTRA_RRC_Definitions.BCCH_DL_SCH_Message
    elif channel == 'UL DCCH':
        msg_obj = RRCLTE.EUTRA_RRC_Definitions.UL_DCCH_Message
    else:
        return {}

    # Loading payload...
    msg_obj.from_uper(
        binascii.unhexlify(''.join(payload.split(' ')).strip()))

    # Decoding message data.
    return json.loads(msg_obj.to_json())


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
        '-t', '%F %H:%M:%S.',  # Time format to use in the pcap file.
        input_txt,  # Input .txt file.
        output_pcap,  # Output .pcap file.
        '-l', str(diss_num)  # Number of the dissector to be called.
    ]

    # Calling text2pcap
    subprocess.check_call(t2p_argc)