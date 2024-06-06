from datetime import datetime
from enum import Enum


# TODO: Add printing errors to file

class NetworkType(Enum):
    LTE = "LTE"
    NR5GSA = "NR5G-SA"
    NR5GNSA = "NR5G-NSA"
    WCDMA = "WCDMA"


class Is_TDD(Enum):
    TDD = "TDD"
    FDD = "FDD"


class UE_State(Enum):
    SEARCH = "SEARCH"
    LIMSRV = "LIMSRV"
    NOCONN = "NOCONN"
    CONNECT = "CONNECT"


class Cell_Type(Enum):
    servingcell = "servingcell"
    neighbourcell = "neighbourcell"
    neighbourcell_intra = "neighbourcell intra"
    neighbourcell_inter = "neighbourcell inter"


class AccesTechnology(Enum):
    GSM = 0
    GSM_Compact = 1
    UTRAN = 2
    UTRAN_HSDPA_HSUPA = 6
    EUTRAN = 7
    CDMA_HDR = 8
    NR_5GCN = 11
    NGRAN = 12
    EUTRA_NR = 13


class QENGServing:
    """
    This class holds all data received from the response of the AT+QENG="servingcell" command.
    Most of the data isn't used in the measurements. Data is stored in the format given by the command response,
    so some of the numbers might not represent their real value (for example RSSI here is multiplied by 10)
    """

    def __init__(self, timestamp: datetime,
                 cell_type: Cell_Type, state: UE_State, network_type: NetworkType = NetworkType.LTE,
                 is_tdd: Is_TDD = Is_TDD.TDD,
                 mcc: int = 0, mnc: int = 0,
                 cell_id: str = "", pcid: int = 0, earfcn: str = "",
                 freq_band_ind: int = 0,
                 ul_bandwidth: int = 0, dl_bandwidth: int = 0,
                 tac: str = "0x0", rsrp: int = -0, rsrq: int = -0, rssi: int = -0, sinr: int = 0,
                 cqi: int = 1,
                 tx_power: int = 0, srxlev: int = 0,
                 arfcn: str = "", band: str = "",
                 nr_dl_bandwidth: int = 0,
                 scs: int = 0
                 ):
        self.timestamp = timestamp
        self.cell_type = cell_type
        """Must be servingcell in this class"""
        self.state = state
        self.network_type = network_type
        self.is_tdd = is_tdd
        """Network mode. It has same values for both LTE and 5G NR SA"""
        self.mcc = mcc
        """16-bit unsigned integer. Mobile Country Code (first part of the PLMN code)."""
        self.mnc = mnc
        """16-bit unsigned integer. Mobile Network Code (second part of the PLMN code)."""
        self.cell_id = cell_id
        """Integer type. Cell ID. The parameter determines the 28-bit (UMTS, LTE) or 36-bit (5G NR) cell ID. Range: 
        0–0xFFFFFFFFF"""
        self.pcid = pcid
        """Number format. Physical cell ID."""
        self.earfcn = earfcn
        """The parameter determines the E-UTRA-ARFCN of the cell that was scanned."""
        self.freq_band_ind = freq_band_ind
        """Integer type. E-UTRA frequency band (see 3GPP 36.101)"""
        self.ul_bandwidth = ul_bandwidth
        """Integer type. UL bandwidth. 0 1.4 MHz; 1 3 MHz; 2 5 MHz; 3 10 MHz; 4 15 MHz; 5 20 MHz"""
        self.dl_bandwidth = dl_bandwidth
        """Integer type. DL bandwidth. 0 1.4 MHz; 1 3 MHz; 2 5 MHz; 3 10 MHz; 4 15 MHz; 5 20 MHz"""
        self.tac = tac
        """Tracking Area Code (hexadecimal string) (see 3GPP 23.003 Section 19.4.2.3)."""
        self.rsrp = rsrp
        """16-bit signed integer.
        It indicates the signal of Reference Signal Received Power (see 3GPP
        36.214). Range: -140 to -44 dBm. The closer to -44, the better the signal is.
        The closer to -140, the worse the signal is.
        Multiplied by 10 from actual value."""
        self.rsrq = rsrq
        """It indicates the signal of current Reference Signal Received Quality
        (see 3GPP 36.214). Range: -20 to -3 dB. The closer to -3, the better the
        signal is. The closer to -20, the worse the signal is.
        Multiplied by 10 from actual value."""
        self.rssi = rssi
        """LTE Received Signal Strength Indication. Multiplied by 10 from actual value."""
        self.sinr = sinr
        """Not documented correctly for SIM8262E. SINR value is actually given directly and also is equal to RSSNR value
        given by AT+CPSI? command"""
        self.cqi = cqi
        """Integer type. Channel Quality Indication. Range: 1–30."""
        self.tx_power = tx_power
        """TX power value in dBm (converted from 1/10 given). It is the maximum of all UL channel TX power. 
        The <tx_power> value is only meaningful when the device is in traffic."""
        self.srxlev = srxlev

        # 5G NSA related
        self.arfcn = arfcn
        """Indicates the SA-ARFCN of the cell that was scanned."""
        self.band = band
        """32-bit unsigned integer. Frequency band in 5G NR SA network mode."""
        self.nr_dl_bandwidth = nr_dl_bandwidth
        """Integer type. DL bandwidth. (The value is only valid in RRC connected state.). Values go from 5 MHz at 0 
        to 400 MHz at 14"""
        self.scs = scs
        """NR sub-carrier space. 0 15 kHz; 1 30 kHz; 2 60 kHz; 3 120 kHz; 4 240 kHz"""

    def to_printable_string(self) -> str:
        result: str = "MEASURE_SERVING|"
        result += str(self.timestamp) + "|"
        result += self.network_type.value + "|"
        result += self.tac + "|"
        result += self.cell_id + "|"
        result += str(self.mcc) + "|"
        result += str(self.mnc) + "|"
        result += str(self.pcid) + "|"
        if self.network_type == NetworkType.LTE:
            # earfcn and band are in wrong order in the AT response so this is earfcn
            result += str(self.freq_band_ind) + "|"
        else:
            result += self.arfcn + "|"
        result += str(self.rsrq / 10) + "|"
        result += str(self.rsrp / 10) + "|"
        # RSSI only in LTE mode
        if self.network_type == NetworkType.LTE:
            result += str(self.rssi / 10) + "|"
        else:
            result += "NONE|"
        # I'm not sure if formula applies to all SINR or only LTE
        # if self.network_type == NetworkType.LTE:
        #     result += str((1 / 5) * self.sinr * 10 - 20)
        # else:
        result += str(self.sinr)

        return result

    @classmethod
    def from_string(cls, line: str, timestamp: datetime = None):
        """
        Create an instance of QENGServing class from the response of AT+QENG command\n
        NOTE: This class is only for servingcell response\n
        NOTE: If in EN-DC mode, two calls are necessary to get both LTE and NR5G-NSA data\n
        NOTE: In EN-DC mode the connection state is assumed to be CONNECT, if it's not the case it must be modified manually
        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :param line: line containing the main part of response of AT+QENG command (the one containing network type)
        :return: instance of QENGServing class filled with data extracted from message, None if incorrect format
        """
        cell_type: Cell_Type = Cell_Type.servingcell

        # Remove +QENG: prefix from all lines and split values separated by ','
        # Second strip because spacing after QENG is inconsistent
        values: list[str] = line.strip().removeprefix('+QENG:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        if len(values) < 3:
            # Most likely the first line in EN-DC mode with connection state
            if len(values) == 2:
                return None
                # return values[0], values[1]
            return None

        if "neighbour" in values[0]:
            print('A response from AT+QENG="servingcell" is expected, got a response from AT+QENG="neighbourcell" '
                  'isntead')
            return None

        if timestamp is None:
            timestamp = datetime.now()

        # In EN-DC mode the main line starts with network type instead of servingcell
        if values[0] == "servingcell":
            cell_type = Cell_Type.servingcell
            ue_state: UE_State = UE_State(values[1])
            if ue_state != UE_State.CONNECT:
                return cls(timestamp=timestamp, cell_type=cell_type, state=ue_state)

            match values[2]:
                case "LTE":
                    if len(values) != 20:
                        print("Incorrect amount of values in response line: got " + str(len(values))
                              + " but 20 are expected for LTE")
                        return None
                    # checks like if (cqi > 0 and cqi < 31) could be added, but I think it's safe enough to assume that
                    # if the beginning is correct the rest is as well
                    return cls(timestamp=timestamp,
                               cell_type=cell_type, state=ue_state, network_type=NetworkType(values[2]),
                               is_tdd=Is_TDD(values[3]), mcc=int(values[4]), mnc=int(values[5]),
                               cell_id=values[6], pcid=int(values[7]), earfcn=values[8],
                               freq_band_ind=int(values[9]), ul_bandwidth=int(values[10]), dl_bandwidth=int(values[11]),
                               tac=values[12], rsrp=int(values[13]), rsrq=int(values[14]), rssi=int(values[15]),
                               sinr=int(values[16]), cqi=int(values[17]), tx_power=int(values[18]),
                               srxlev=int(values[19]))

                case "NR5G-SA":
                    if len(values) != 17:
                        print("Incorrect amount of values in response line: got " + str(len(values))
                              + " but 17 are expected for NR5G-SA")
                        return None
                    return cls(timestamp=timestamp,
                               cell_type=cell_type, state=ue_state, network_type=NetworkType(values[2]),
                               is_tdd=Is_TDD(values[3]), mcc=int(values[4]), mnc=int(values[5]),
                               cell_id=values[6], pcid=int(values[7]), tac=values[8], arfcn=values[9],
                               band=values[10], nr_dl_bandwidth=int(values[11]),
                               rsrp=int(values[12]), rsrq=int(values[13]), sinr=int(values[14]),
                               scs=int(values[15]), srxlev=int(values[16])
                               )
                case "WCDMA":
                    # We're not interested in 3G for this project
                    return None
                case _:
                    print("Unknown network type: " + values[2])
                    return None

        # In EN-DC mode
        else:
            if values[0] == "LTE":
                if len(values) != 18:
                    print("Incorrect amount of values in response line: got " + str(len(values))
                          + " but 18 are expected for LTE in EN-DC mode")
                    return None
                return cls(timestamp=timestamp,
                           cell_type=cell_type, state=UE_State.CONNECT, network_type=NetworkType("LTE"),
                           is_tdd=Is_TDD(values[1]), mcc=int(values[2]), mnc=int(values[3]),
                           cell_id=values[4], pcid=int(values[5]), earfcn=values[6],
                           freq_band_ind=int(values[7]), ul_bandwidth=int(values[8]), dl_bandwidth=int(values[9]),
                           tac=values[10], rsrp=int(values[11]), rsrq=int(values[12]), rssi=int(values[13]),
                           sinr=int(values[14]), cqi=int(values[15]), tx_power=int(values[16]),
                           srxlev=int(values[17])
                           )

            elif values[0] == "NR5G-NSA":
                if len(values) != 11:
                    print("Incorrect amount of values in response line: got " + str(len(values))
                          + " but 11 are expected for LTE")
                    return None
                return cls(timestamp=timestamp,
                           cell_type=cell_type, state=UE_State.CONNECT, network_type=NetworkType("NR5G-NSA"),
                           mcc=int(values[1]), mnc=int(values[2]),
                           pcid=int(values[3]), rsrp=int(values[4]), sinr=int(values[5]), rsrq=int(values[6]),
                           arfcn=values[7], band=values[8], nr_dl_bandwidth=int(values[9]), scs=int(values[10])
                           )
            else:
                print("Unrecognized network type in EN-DC mode: " + values[0])

        return None


class QENGNeighbour:
    """
    This class holds all data received from the response of the AT+QENG="neighbourcell" command.
    Most of the data isn't used in the measurements. Data is stored in the format given by the command response,
    so some of the numbers might not represent their real value (for example RSSI here is multiplied by 10)
    """

    def __init__(self, timestamp: datetime,
                 cell_type: Cell_Type, network_type: NetworkType = NetworkType.LTE,
                 earfcn: int = 0, pcid: int = 0,
                 rsrp: int = -0, rsrq: int = -0, rssi: int = -0, sinr: int = 0,
                 srxlev: int = 0, cell_resel_priority: int = 0, s_non_intra_search: int = 0,
                 thresh_serving_low: int = 0, s_intra_search: int = 0,
                 threshX_low: int = 0, threshX_high: int = 0
                 ):
        self.timestamp = timestamp
        self.cell_type = cell_type
        """Must be a neighbourcell in this class"""
        self.network_type = network_type
        """Must be LTE"""
        self.earfcn = earfcn
        """The parameter determines the E-UTRA-ARFCN of the cell that was scanned."""
        self.pcid = pcid
        """Number format. Physical cell ID."""
        self.rsrp = rsrp
        """16-bit signed integer.
        It indicates the signal of Reference Signal Received Power (see 3GPP
        36.214). Range: -140 to -44 dBm. The closer to -44, the better the signal is.
        The closer to -140, the worse the signal is.
        Multiplied by 10 from actual value."""
        self.rsrq = rsrq
        """It indicates the signal of current Reference Signal Received Quality
        (see 3GPP 36.214). Range: -20 to -3 dB. The closer to -3, the better the
        signal is. The closer to -20, the worse the signal is.
        Multiplied by 10 from actual value."""
        self.rssi = rssi
        """LTE Received Signal Strength Indication. Multiplied by 10 from actual value."""
        self.sinr = sinr
        """Not documented correctly for SIM8262E. For neighbouring cell the sinr value is given but is always 0, it can
        be ignored."""
        self.srxlev = srxlev
        """Select reception level value for base station in dB (see 3GPP 25.304)."""
        self.cell_resel_priority = cell_resel_priority

        # neighbourcell intra exclusive
        """Integer type. Cell reselection priority. Range: 0–7."""
        self.s_non_intra_search = s_non_intra_search
        """Threshold to control non-intra frequency searches."""
        self.thresh_serving_low = thresh_serving_low
        """Specifies the suitable reception level threshold (in dB) used by the UE on the serving cell 
        when reselecting towards a lower priority RAT/frequency."""
        self.s_intra_search = s_intra_search
        """Cell selection parameter for the intra frequency cell."""

        # neighbourcell inter exclusive
        self.threshX_low = threshX_low
        """To be considered for re-selection. The suitable receive level value of an evaluated lower priority 
        cell must be greater than this value."""
        self.threshX_high = threshX_high
        """To be considered for re-selection. The suitable receive level value of an evaluated higher priority 
        cell must be greater than this value."""

    def to_printable_string(self) -> str:
        if self.cell_type == Cell_Type.neighbourcell_intra:
            result: str = "MEASURE_NEIGHBOUR_INTRA|"
        elif self.cell_type == Cell_Type.neighbourcell_inter:
            result: str = "MEASURE_NEIGHBOUR_INTER|"
        else:
            return ""
        result += str(self.timestamp) + "|"
        result += self.network_type.value + "|"
        result += str(self.pcid) + "|"
        result += str(self.earfcn) + "|"
        result += str(self.rsrq / 10) + "|"
        result += str(self.rsrp / 10) + "|"
        result += str(self.rssi / 10)  # + "|"
        # result += str((1 / 5) * self.sinr * 10 - 20)
        # result += str(self.sinr)
        return result

    @classmethod
    def from_string(cls, line: str, timestamp: datetime = None):
        """
        Create an instance of QENGServing class from the response of AT+QENG command\n
        NOTE: This class is only for neighbourcell response\n
        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :param line: line containing the main part of response of AT+QENG command (the one containing network type)
        :return: instance of QENGNeighbour class filled with data extracted from message, None if incorrect format
        """
        # Remove +QENG: prefix from all lines and split values separated by ','
        # Second strip because spacing after QENG can be inconsistent
        values: list[str] = line.strip().removeprefix('+QENG:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        # Should be at least 2 to know network type
        if len(values) < 2:
            print("Incorrect neighbourcell response format (too little values)")
            return None

        cell_type: Cell_Type = Cell_Type(values[0])

        # Simple neighbourcell only for WCDMA which isn't interesting to us
        if cell_type == Cell_Type.neighbourcell or cell_type == Cell_Type.servingcell:
            return None

        if timestamp is None:
            timestamp = datetime.now()

        if cell_type == Cell_Type.neighbourcell_intra:
            if len(values) != 13:
                print("Incorrect amount of values in response line: got " + str(len(values))
                      + " but 13 are expected for neighbourcell intra")
                return None

            return cls(timestamp=timestamp,
                       cell_type=cell_type, network_type=NetworkType(values[1]),
                       earfcn=int(values[2]), pcid=int(values[3]),
                       rsrq=int(values[4]), rsrp=int(values[5]), rssi=int(values[6]), sinr=int(values[7]),
                       srxlev=int(values[8]), cell_resel_priority=int(values[9]),
                       s_non_intra_search=int(values[10]), thresh_serving_low=int(values[11]),
                       s_intra_search=int(values[12])
                       )

        elif cell_type == Cell_Type.neighbourcell_inter:
            if len(values) != 12:
                print("Incorrect amount of values in response line: got " + str(len(values))
                      + " but 12 are expected for neighbourcell intra")
                return None

            return cls(timestamp=timestamp,
                       cell_type=cell_type, network_type=NetworkType(values[1]),
                       earfcn=int(values[2]), pcid=int(values[3]),
                       rsrq=int(values[4]), rsrp=int(values[5]), rssi=int(values[6]), sinr=int(values[7]),
                       srxlev=int(values[8]), cell_resel_priority=int(values[9]),
                       threshX_low=int(values[10]), threshX_high=int(values[11])
                       )

        return None


def prefix_with_zeros(left_digits: int, nb: str, sep: str = ".") -> str:
    """Prefixes nb with 0 until it has `left_digits` amount of digits in the left part
    :param left_digits: Amount of digits nb is supposed to have on the left part
    :param nb: floating number as string where left and right parts are separated by `sep`
    :param sep: separator of the number
    :return: given number prefixed with 0 to have `left_digits` digits in the left part
    """
    parts = nb.split(sep)
    left = parts[0]
    right = parts[1]
    if len(left) < left_digits:
        for i in range(left_digits - len(left)):
            left = "0" + left
    return left + sep + right


class CGPSINFO:
    """
    +CGPSINFO:[<lat>],[<N/S>],[<log>],[<E/W>],[<date>],[<UTCtime>],[<alt>],[<speed>],[<course>]
    This class holds all data received from the response of the AT+CGPSINFO command.
    """

    def __init__(self, timestamp: datetime,
                 lat: str = "", ns: str = "", log: str = "", ew: str = "",
                 date: str = "", utc_time: str = "",
                 alt: float = 0, speed: float = 0, course: float = 0
                 ):
        self.timestamp = timestamp
        self.lat = lat
        """Latitude of current position. Output format is in DMS coordinates (ddmm.mmmmmm)"""
        self.ns = ns
        """N/S Indicator, N=north or S=south"""
        self.log = log
        """Longitude of current position. Output format is in DMS coordinates (dddmm.mmmmmm)"""
        self.ew = ew
        """E/W Indicator, E=east or W=west"""
        self.date = date
        """Date. Output format is ddmmyy"""
        self.utc_time = utc_time
        """UTC Time. Output format is hhmmss.s"""
        self.alt = alt
        """MSL Altitude. Unit is meters."""
        self.speed = speed
        """Speed Over Ground. Unit is knots."""
        self.course = course
        """Course. Degrees."""

    def to_printable_string(self) -> str:
        result: str = "GPS|"
        result += str(self.timestamp) + "|"
        if self.lat == "":
            result += "||"
        else:
            result += str(self.__convert_lat_to_decimal()) + "|"
            result += str(self.__convert_long_to_decimal()) + "|"
            result += str(self.alt)
        return result

    def __convert_lat_to_decimal(self) -> float:
        """
        Converts the latitude in the format given by the AT command (ddmm.mmmmmm) to the decimal coordinate
        format. Hemisphere indicator decides if output is negative or positive.
        :return: Latitude in decimal format
        """
        degrees: int = int(self.lat[0] + self.lat[1])
        minutes: float = float(self.lat[2:])
        if self.ns == "N":
            # 7 digits are sufficient to store coordinates with centimeter accuracy
            return round(degrees+minutes/60, 7)
        elif self.ns == "S":
            return round(-(degrees + minutes / 60), 7)
        else:
            return 0

        # +CGPSINFO: 4807.186165,N,137.772582,W,060624,141328.0,85.1,0.0,0.0

    def __convert_long_to_decimal(self) -> float:
        """Converts the longitude in the format given by the AT command (dddmm.mmmmmm) to the decimal coordinate
        format. Hemisphere indicator decides if output is negative or positive.
        :return: Longitude in decimal format
        """
        # The big problem here is the fact that not all ddd are present.
        # For example 1°37' would be represented as 137. instead of 00137.
        parts = self.log.split('.')
        left = parts[0]
        if len(parts) < 5:
            for i in range(5-len(parts)):
                left = "0"+left

        degrees: int = int(self.log[0] + self.log[1] + self.log[2])
        minutes: float = float(self.log[3:])
        if self.ew == "E":
            return round(degrees + minutes / 60, 7)
        elif self.ew == "W":
            return round(-(degrees + minutes / 60), 7)
        else:
            return 0

    @classmethod
    def from_string(cls, line: str, timestamp: datetime = None):
        """
        Create an instance of CGPSINFO class from the response of AT+CGPSINFO command\n
        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :param line: line containing the main part of response of AT+CGPSINFO command
        :return: instance of CGPSINFO class filled with data extracted from message, None if incorrect format
        """
        # Remove +CGPSINFO: prefix from all lines and split values separated by ','
        # Second strip because spacing after CGPSINFO can be inconsistent
        values: list[str] = line.strip().removeprefix('+CGPSINFO:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        if len(values) != 9:
            print("Incorrect CGPSINFO response format (not enough values found)")
            return None

        # If empty string most likely no GPS info was given by the response
        if values[0] == "":
            # return None
            return cls(timestamp=timestamp)

        return cls(timestamp=timestamp,
                   lat=prefix_with_zeros(nb=values[0], left_digits=4), ns=values[1],
                   log=prefix_with_zeros(nb=values[2], left_digits=5), ew=values[3],
                   date=values[4], utc_time=values[5],
                   alt=float(values[6]), speed=float(values[7]), course=float(values[8])
                   )


class COPS:
    """
    +COPS: <mode>[,<format>,<oper>[,< AcT>]]
    Example: +COPS: 0,0,"F SFR",7
    This class is used to extract the name of the operator using AT+COPS? command
    """

    # Timestamp is not necessary as it's only used once in the beginning
    def __init__(self,
                 mode: int = 0, oper_format: int = 0,
                 oper: str = "", act: AccesTechnology = AccesTechnology.EUTRAN,
                 ):
        self.mode = mode
        """0 automatic; 1 manual; 2 force deregister; 3 set only <format> 4; manual/automatic"""
        self.format = oper_format
        """0 long format alphanumeric <oper>; 1 short format alphanumeric <oper>; 2 numeric <oper>"""
        self.oper = oper
        """string type, <format> indicates if the format is alphanumeric or numeric."""
        self.act = act
        """Access technology selected 0 GSM; 1 GSM Compact; 2 UTRAN; 6 UTRAN_HSDPA_HSUPA
        7 EUTRAN; 8 CDMA/HDR; 11 NR_5GCN (NR connected to 5G core Network)
        12 NGRAN (NG-RAN access technology); 13 EUTRA_NR (Dual connectivity of LTE with NR)
        """

    def to_printable_string(self) -> str:
        result: str = "OPERATOR|"
        if self.format == 0 or self.format == 1:
            result += self.oper + "|"
        # TODO: Numerical format, do something with it
        elif self.format == 3:
            result += self.oper + "|"
        # Incorrect format, return empty
        else:
            result += "|"
            return result

        result += self.act.name
        return result

    @classmethod
    def from_string(cls, line: str):
        """
        Create an instance of COPS class from the response of AT+COPS? command
        :param line: line containing the main part of response of AT+COPS? command
        :return: instance of COPS class filled with data extracted from message, None if couldn't extract info
        """
        # Remove +COPS: prefix from all lines and split values separated by ','
        # Second strip because spacing after COPS can be inconsistent
        values: list[str] = line.strip().removeprefix('+COPS:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        if len(values) != 4:
            print("Incorrect COPS response format (not enough values found)")
            return None

        # Empty string means no operator so no connection
        if values[2] == "":
            return None

        return cls(mode=int(values[0]), oper_format=int(values[1]), oper=values[2], act=AccesTechnology(int(values[3])))
