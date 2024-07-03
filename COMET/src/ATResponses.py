from datetime import datetime
from enum import Enum


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
    UNKNOWN = "UNKNOWN"


class Cell_Type(Enum):
    servingcell = "servingcell"
    neighbourcell = "neighbourcell"
    neighbourcell_intra = "neighbourcell intra"
    neighbourcell_inter = "neighbourcell inter"
    unknown = "unknown"


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
    UNKNOWN = 15  # 15 appears in AT+COPS? when forced in NR5G only mode, but it doesn't appear in the manual


class QENGServing:
    """
    Manages the information gathered from the AT+QENG="servingcell" command

    Data is stored in the format given by the command response,
    so some of the numbers might not represent their real value
    (for example RSSI here is multiplied by 10 from actual value)

    Part of the data (like `ul_bandwidth` or `tx_power`) won't be saved to the measurement file but is still saved
    in the class instance.

    Example:
            >>> info = QENGServing.from_string('+QENG:"servingcell","CONNECT","LTE","FDD",208,10,158800132,82,'
            >>> 'EUTRAN-BAND3,1501,5,5,0xC0FA,-1102,-200,-659,-10,0,-99,19')
            >>> info.to_printable_string()
            >>> 'MEASURE_SERVING|2024-06-11 15:16:14|LTE|0xC0FA|158800132|208|10|82|1501|-20.0|-110.2|-65.9|-10'
            >>> info.state
            >>> UE_State.CONNECT
    """

    def __init__(self, timestamp: datetime,
                 cell_type: Cell_Type = Cell_Type.servingcell,
                 state: UE_State = UE_State.UNKNOWN, network_type: NetworkType = NetworkType.LTE,
                 is_tdd: Is_TDD = Is_TDD.TDD, mcc: int = -1, mnc: int = -1,
                 cell_id: str = "", pcid: int = -1, earfcn: str = "", freq_band_ind: int = -1,
                 ul_bandwidth: int = -1, dl_bandwidth: int = -1,
                 tac: str = "", rsrp: int = -0, rsrq: int = -0, rssi: int = -0, sinr: int = -1,
                 cqi: int = -1, tx_power: int = -1, srxlev: int = -1,
                 arfcn: str = "", band: str = "", nr_dl_bandwidth: int = -1,
                 scs: int = -1, is_en_dc: bool = False
                 ):
        # TODO: Add 5G SA stuff
        self.timestamp = timestamp
        self.cell_type = cell_type
        """Must be servingcell in this class"""
        self.state = state
        self.network_type = network_type
        self.is_tdd = is_tdd
        """Network mode. It has same values for both LTE and 5G NR SA ('TDD' or 'FDD')"""
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

        self.is_en_dc = is_en_dc
        """Indicates if the response was given while in EN-DC mode if True"""

    def to_printable_string(self) -> str:
        """Uses QENGServing instance data to return a string in a format printable to a measurement file.

        Examples:
            >>> info = QENGServing.from_string('+QENG:"servingcell","CONNECT","LTE","FDD",208,10,158800132,82,'
            >>> 'EUTRAN-BAND3,1501,5,5,0xC0FA,-1102,-200,-659,-10,0,-99,19')
            >>> info.to_printable_string()
            >>> 'MEASURE_SERVING|2024-06-11 15:16:14|LTE|0xC0FA|158800132|208|10|82|1501|-20.0|-110.2|-65.9|-10'

        :return: String in the format
            'MEASURE_SERVING|TIMESTAMP|NETWORK_TYPE|TAC|CELLID|MCC|MNC|PCID|EARFCN|RSRQ|RSRP|RSSI|SINR|IS_EN_DC'
        """
        if self.state == UE_State.UNKNOWN:
            return f"MEASURE_SERVING|{str(self.timestamp)}|||||||||||"

        if self.network_type == NetworkType.WCDMA:
            return f"MEASURE_SERVING|{str(self.timestamp)}|||||||||||"

        earfcn = "NONE"
        rsrq = str(self.rsrq / 10)
        rsrp = str(self.rsrp / 10)
        rssi = "NONE"  # No RSSI in 5G-NSA or 5G-SA
        en_dc = "NO"
        if self.is_en_dc:
            en_dc = "YES"
        if self.network_type == NetworkType.LTE:
            rssi = str(self.rssi / 10)
            # earfcn and band are in wrong order in the AT response for LTE so this is earfcn
            earfcn = str(self.freq_band_ind)
        elif self.network_type == NetworkType.NR5GNSA or self.network_type == NetworkType.NR5GSA:
            earfcn = self.arfcn

        return (f"MEASURE_SERVING|{str(self.timestamp)}|{self.network_type.value}|{self.tac}|{self.cell_id}|"
                f"{str(self.mcc)}|{str(self.mnc)}|{str(self.pcid)}|{earfcn}|"
                f"{rsrq}|{rsrp}|{rssi}|{str(self.sinr)}|{en_dc}")

    @staticmethod
    def get_ue_state_from_response(response_line: str) -> UE_State | None:
        """
        Extract the UE State from the first line of AT+QENG="servingcell" response when in EN-DC mode.

        :param response_line: the first line of AT+QENG="servingcell" response when in EN-DC mode.
            The line must be in the following format: '+QENG: "servingcell",<state>'
        :return: The UE_State enum corresponding to the UE state or None if response_line is in wrong format
        """
        line = response_line.strip()
        if not line.startswith("+QENG"):
            print(f"Wrong format for EN-DC UE state line, got: {response_line}")
            return None
        values: list[str] = line.removeprefix('+QENG:').replace('"', '').strip().split(',')
        if len(values) != 2 or values[1] != "servingcell":
            print(f"Wrong format for EN-DC UE state line, got: {response_line}")
            return None

        return UE_State(values[1])

    @classmethod
    def from_string(cls, line: str, timestamp: datetime = None, en_dc_ue_mode: UE_State = None):
        """
        Create an instance of QENGServing class from the response of AT+QENG="servingcell" command

        Works only when module is on 5G SA, LTE or 5G NSA+LTE in EN-DC mode. When in EN-DC mode,
        this method must be called separately for both components (5G-NSA and LTE).

        In EN-DC mode the UE connection state is defined by the `en_dc_ue_mode` parameter
        and is assumed to be CONNECT by default (when None).

        Example:
            >>> info = QENGServing.from_string('+QENG:"servingcell","CONNECT","LTE","FDD",208,10,158800132,82,'
            >>> 'EUTRAN-BAND3,1501,5,5,0xC0FA,-1102,-200,-659,-10,0,-99,19')
            >>> info.to_printable_string()
            >>> 'MEASURE_SERVING|2024-06-11 15:16:14|LTE|0xC0FA|158800132|208|10|82|1501|-20.0|-110.2|-65.9|-10'
            >>> info.state
            >>> UE_State.CONNECT

        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :param line: line containing the main part of response of AT+QENG command (the one containing network type).
            The line format depends on the cell network mode, the format can be found in the AT commands manual
        :param en_dc_ue_mode: The UE state in EN-DC mode from the first line of the command response. When None,
            the UE state is assumed to be CONNECT

        :return: an instance will all relevant data extracted from the given line of response
            or None if the line format is incorrect or if network type is WCDMA
            or an empty instance evaluating to False with UNKNOWN UE state when no network connection
        """
        if timestamp is None:
            timestamp = datetime.now()

        if "ERROR" in line:  # When no network connection AT+QENG returns ERROR
            return cls(timestamp=timestamp)

        # Remove +QENG: prefix from all lines and split values separated by ','
        # Second strip because spacing after QENG is inconsistent
        values: list[str] = line.strip().removeprefix('+QENG:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        nb_params = len(values)

        # Different network types give different amount of parameters,
        # if it doesn't match it's probably in the wrong format
        if nb_params == 20:  # LTE
            if values[0] != "servingcell":
                print(f'Unrecognized parameter: "servingcell" was expected but {values[0]} was given)')
                print(f'The line given was: {line}')
                return None
            try:
                return cls(timestamp=timestamp,
                           cell_type=Cell_Type.servingcell, state=UE_State(values[1]),
                           network_type=NetworkType(values[2]), is_tdd=Is_TDD(values[3]),
                           mcc=int(values[4]), mnc=int(values[5]), cell_id=values[6],
                           pcid=int(values[7]), earfcn=values[8],
                           freq_band_ind=int(values[9]), ul_bandwidth=int(values[10]), dl_bandwidth=int(values[11]),
                           tac=values[12], rsrp=int(values[13]), rsrq=int(values[14]), rssi=int(values[15]),
                           sinr=int(values[16]), cqi=int(values[17]), tx_power=int(values[18]),
                           srxlev=int(values[19]))
            except ValueError:
                print(f"One of the parameters in line had incorrect format: {line}")
        elif nb_params == 17:  # 5G-SA or 3G
            # If on 3G, return None, we want to ignore it
            if values[2] == "WCDMA":
                return None
            if values[0] != "servingcell":
                print(f'Unrecognized parameter: "servingcell" was expected but {values[0]} was given)')
                print(f'The line given was: {line}')
                return None

            try:
                return cls(timestamp=timestamp,
                           cell_type=Cell_Type.servingcell, state=UE_State(values[1]),
                           network_type=NetworkType(values[2]), is_tdd=Is_TDD(values[3]),
                           mcc=int(values[4]), mnc=int(values[5]), cell_id=values[6], pcid=int(values[7]),
                           tac=values[8], arfcn=values[9],
                           band=values[10], nr_dl_bandwidth=int(values[11]),
                           rsrp=int(values[12]), rsrq=int(values[13]), sinr=int(values[14]),
                           scs=int(values[15]), srxlev=int(values[16])
                           )
            except ValueError:
                print(f"One of the parameters in line had incorrect format: {line}")

        elif nb_params == 11:  # 5G-NSA in EN-DC mode
            if values[0] != "NR5G-NSA":
                print(f'Unrecognized parameter: "NR5G-NSA" was expected but {values[0]} was given)')
                print(f'The line given was: {line}')
                return None

            ue_state = en_dc_ue_mode
            if ue_state is None:
                ue_state = UE_State.CONNECT

            try:
                return cls(timestamp=timestamp,
                           cell_type=Cell_Type.servingcell, state=ue_state, network_type=NetworkType("NR5G-NSA"),
                           mcc=int(values[1]), mnc=int(values[2]),
                           pcid=int(values[3]), rsrp=int(values[4]), sinr=int(values[5]), rsrq=int(values[6]),
                           arfcn=values[7], band=values[8], nr_dl_bandwidth=int(values[9]), scs=int(values[10]),
                           is_en_dc=True
                           )
            except ValueError:
                print(f"One of the parameters in line had incorrect format: {line}")
        elif nb_params == 18:  # LTE in EN-DC mode
            if values[0] != "LTE":
                print(f'Unrecognized parameter: "LTE" was expected but {values[0]} was given)')
                print(f'The line given was: {line}')
                return None

            ue_state = en_dc_ue_mode
            if ue_state is None:
                ue_state = UE_State.CONNECT

            try:
                return cls(timestamp=timestamp,
                           cell_type=Cell_Type.servingcell, state=ue_state, network_type=NetworkType("LTE"),
                           is_tdd=Is_TDD(values[1]), mcc=int(values[2]), mnc=int(values[3]),
                           cell_id=values[4], pcid=int(values[5]), earfcn=values[6],
                           freq_band_ind=int(values[7]), ul_bandwidth=int(values[8]), dl_bandwidth=int(values[9]),
                           tac=values[10], rsrp=int(values[11]), rsrq=int(values[12]), rssi=int(values[13]),
                           sinr=int(values[14]), cqi=int(values[15]), tx_power=int(values[16]),
                           srxlev=int(values[17]), is_en_dc=True
                           )
            except ValueError:
                print(f"One of the parameters in line had incorrect format: {line}")

        else:
            print(f'Incorrect AT+QENG="servingcell" response format (unrecognized number of parameter: {nb_params})')
            print(f'The line given was: {line}')
            return None

    def __bool__(self):
        """
        Evaluates to True if is connected to network
        """
        return self.state != UE_State.UNKNOWN


class QENGNeighbour:
    """
    Manages the information gathered from the AT+QENG="neighbourcell" command

    Data is stored in the format given by the command response,
    so some of the numbers might not represent their real value
    (for example RSSI here is multiplied by 10 from actual value)

    Part of the data (like `srxlev` or `s_intra_search`) won't be saved to the measurement file but is still saved
    in the class instance.

    This class doesn't provide attributes for WCDMA responses

    Example:
            >>> info = QENGNeighbour.from_string('+QENG:"neighbourcell intra","LTE",1501,75,-200,-1116,-690,0,18,'
            >>> '5,62,8,62')
            >>> info.to_printable_string()
            >>> 'MEASURE_NEIGHBOUR_INTRA|2024-06-11 15:16:14|LTE|75|1501|-20.0|-111.6|-69.0'
            >>> info.s_intra_search
            >>> 62
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
        """Uses QENGNeighbour instance data to return a string in a format printable to a measurement file.

        Examples:
            >>> info = QENGNeighbour.from_string('+QENG:"neighbourcell intra","LTE",1501,75,-200,-1116,-690,0,18,'
            >>> '5,62,8,62')
            >>> info.to_printable_string()
            >>> 'MEASURE_NEIGHBOUR_INTRA|2024-06-11 15:16:14|LTE|75|1501|-20.0|-111.6|-69.0'

        :return: String in the format
            'MEASURE_NEIGHBOUR_INTRA|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI'
            or
            'MEASURE_NEIGHBOUR_INTER|TIMESTAMP|NETWORK_TYPE|PCID|EARFCN|RSRQ|RSRP|RSSI'
        """
        if self.cell_type == Cell_Type.neighbourcell_intra:
            measurement_type = "MEASURE_NEIGHBOUR_INTRA"
        elif self.cell_type == Cell_Type.neighbourcell_inter:
            measurement_type = "MEASURE_NEIGHBOUR_INTER"
        else:
            return ""

        return (f"{measurement_type}|{str(self.timestamp)}|{self.network_type.value}|{str(self.pcid)}|"
                f"{str(self.earfcn)}|{str(self.rsrq / 10)}|{str(self.rsrp / 10)}|{str(self.rssi / 10)}")

    @classmethod
    def from_string(cls, line: str, timestamp: datetime = None):
        """
        Create an instance of QENGNeighbour class from the response of AT+QENG="neighbourcell" command

        This method must be applied separately to each line of response of AT+QENG="neighbourcell" command.

        When in WCDMA mode, always returns empty instances evaluating to False.
        When in LTE mode, WCDMA entries are returned as empty instances evaluating to False.

        Example:
            >>> info = QENGNeighbour.from_string('+QENG:"neighbourcell intra","LTE",1501,75,-200,-1116,-690,0,18,'
            >>> '5,62,8,62')
            >>> info.to_printable_string()
            >>> 'MEASURE_NEIGHBOUR_INTRA|2024-06-11 15:16:14|LTE|75|1501|-20.0|-111.6|-69.0'
            >>> info.s_intra_search
            >>> 62

        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :param line: a line from AT+QENG="neighbourcell" response.
            The line format can be found in the AT commands manual

        :return: An instance will all relevant data extracted from the given line of response.
            None if the line format is incorrect.
            An empty (and evaluating to False) instance if in WCDMA mode and for WCDMA entries in LTE mode.
        """
        if "ERROR" in line:  # We're not interested in neighbours when there is no network
            return None

        # Remove +QENG: prefix from all lines and split values separated by ','
        # Second strip because spacing after QENG can be inconsistent
        values: list[str] = line.strip().removeprefix('+QENG:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        if timestamp is None:
            timestamp = datetime.now()

        nb_params = len(values)
        if nb_params == 13:  # LTE neighbourcell intra
            try:
                return cls(timestamp=timestamp,
                           cell_type=Cell_Type(values[0]), network_type=NetworkType(values[1]),
                           earfcn=int(values[2]), pcid=int(values[3]),
                           rsrq=int(values[4]), rsrp=int(values[5]), rssi=int(values[6]), sinr=int(values[7]),
                           srxlev=int(values[8]), cell_resel_priority=int(values[9]),
                           s_non_intra_search=int(values[10]), thresh_serving_low=int(values[11]),
                           s_intra_search=int(values[12])
                           )
            except ValueError:
                print(f"One of the parameters in line had incorrect format: {line}")

        elif nb_params == 12:  # LTE neighbourcell inter
            try:
                return cls(timestamp=timestamp,
                           cell_type=Cell_Type(values[0]), network_type=NetworkType(values[1]),
                           earfcn=int(values[2]), pcid=int(values[3]),
                           rsrq=int(values[4]), rsrp=int(values[5]), rssi=int(values[6]), sinr=int(values[7]),
                           srxlev=int(values[8]), cell_resel_priority=int(values[9]),
                           threshX_low=int(values[10]), threshX_high=int(values[11])
                           )
            except ValueError:
                print(f"One of the parameters in line had incorrect format: {line}")
        elif nb_params == 10:  # WCDMA, return instance with empty values
            return cls(timestamp=timestamp, cell_type=Cell_Type.neighbourcell)
        elif nb_params == 7:  # LTE in WCDMA mode, return instance with empty values
            return cls(timestamp=timestamp, cell_type=Cell_Type.neighbourcell)
        else:
            print(f'Incorrect AT+QENG="neighbourcell" response format (unrecognized number of parameter: {nb_params})')
            print(f'The line given was: {line}')
            return None

    def __bool__(self):
        """
        Evaluates to false when cell type is neighbourcell (in WCDMA mode)
        """
        return self.cell_type == Cell_Type.neighbourcell_inter or self.cell_type == Cell_Type.neighbourcell_intra


class CGPSINFO:
    """
    Manages the information gathered from the AT+CGPSINFO command

    Example:
        >>> info = CGPSINFO.from_string('+CGPSINFO: 4807.190267,N,137.755623,W,010624,132225.0,113.0,0.0,0.0',
        >>> datetime.now())
        >>> info.to_printable_string()
        >>> 'GPS|2024-06-11 15:16:14|48.119814|-1.6295829|113.0'
        >>> info.lat
        >>> '4807.190267'
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
        """
        Uses CGPSINFO instance data to return a string in a format printable to a measurement file.

        Examples:
            >>> info = CGPSINFO.from_string('+CGPSINFO: 4807.190267,N,137.755623,W,010624,132225.0,113.0,0.0,0.0',
            >>> datetime.now())
            >>> info.to_printable_string()
            >>> 'GPS|2024-06-11 15:16:14|48.119814|-1.6295829|113.0'

            >>> info = CGPSINFO.from_string('+CGPSINFO: ,,,,,,,,', datetime.now())
            >>> info.to_printable_string()
            >>> 'GPS|2024-06-11 15:16:14|||'

        :return: String in the format GPS|TIMESTAMP|LATITUDE|LONGITUDE|ALTITUDE
        """
        if self.lat == "":
            return f"GPS|{str(self.timestamp)}|||"

        lat = str(self.__convert_lat_to_decimal())
        long = str(self.__convert_long_to_decimal())
        return f"GPS|{str(self.timestamp)}|{lat}|{long}|{str(self.alt)}"

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
            return round(degrees + minutes / 60, 7)
        elif self.ns == "S":
            return round(-(degrees + minutes / 60), 7)
        else:
            return 0

    def __convert_long_to_decimal(self) -> float:
        """
        Converts the longitude in the format given by the AT command (dddmm.mmmmmm) to the decimal coordinate
        format. Hemisphere indicator decides if output is negative or positive.
        :return: Longitude in decimal format
        """
        # The big problem here is the fact that not all ddd are present.
        # For example 1°37' would be represented as 137. instead of 00137.
        parts = self.log.split('.')
        left = parts[0]
        if len(parts) < 5:
            for i in range(5 - len(parts)):
                left = "0" + left

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
        Create an instance of CGPSINFO class from the response of AT+CGPSINFO command

        The AT+CGPSINFO response must have the following format:
           +CGPSINFO:[<lat>],[<N/S>],[<log>],[<E/W>],[<date>],[<UTCtime>],[<alt>],[<speed>],[<course>]
        If the line format is wrong, None will be returned.
        If the format is correct but values are empty, an instance evaluating to False will be returned

        Examples:
            >>> info = CGPSINFO.from_string('+CGPSINFO: 4807.190267,N,137.755623,W,010624,132225.0,113.0,0.0,0.0',
            >>> datetime.now())
            >>> info.to_printable_string()
            >>> 'GPS|2024-06-11 15:16:14|48.119814|-1.6295829|113.0'

            >>> info = CGPSINFO.from_string('+CGPSINFO: ,,,,,,,,', datetime.now())
            >>> info.to_printable_string()
            >>> 'GPS|2024-06-11 15:16:14|||'

        :param timestamp: Defines the timestamp of the measurement. If None, uses datetime.now() as timestamp.
        :param line: line containing the main part of response of AT+CGPSINFO command
        :return: instance of CGPSINFO class filled with data extracted from message, None if incorrect format
        """
        # Remove +CGPSINFO: prefix from all lines and split values separated by ','
        # Second strip because spacing after CGPSINFO can be inconsistent
        values: list[str] = line.strip().removeprefix('+CGPSINFO:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        _timestamp = timestamp
        if _timestamp is None:
            _timestamp = datetime.now()

        if len(values) != 9:
            print(f"Incorrect AT+CGPSINFO response format (9 values expected, {len(values)} found)")
            print(f"The AT+CGPSINFO response was: {line}")
            return None

        # If latitude is an empty string then no GPS info was given by the response
        if values[0] == "":
            return cls(timestamp=_timestamp)

        try:
            return cls(timestamp=_timestamp,
                       lat=CGPSINFO.prefix_with_zeros(nb=values[0], left_digits=4), ns=values[1],
                       log=CGPSINFO.prefix_with_zeros(nb=values[2], left_digits=5), ew=values[3],
                       date=values[4], utc_time=values[5],
                       alt=float(values[6]), speed=float(values[7]), course=float(values[8])
                       )
        except ValueError:
            print(f"One of the parameters in line had incorrect format: {line}")

    @staticmethod
    def prefix_with_zeros(left_digits: int, nb: str, sep: str = ".") -> str:
        """Prefixes `nb` with 0 until it has `left_digits` amount of digits in the left part

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

    def __bool__(self):
        """
        Evaluates to True if the instance contains meaningful localisation info (non-empty values)
        """
        return self.lat != ""


class COPS:
    """
    Manages the information gathered from the AT+COPS? command

    Example:
            >>> info = COPS.from_string('+COPS: 0,0,"F SFR",7')
            >>> info.to_printable_string()
            >>> 'OPERATOR|F SFR'
            >>> info.act
            >>> AccesTechnology.EUTRAN
    """

    def __init__(self,
                 mode: int = 0, oper_format: int = 0,
                 oper: str = "Unknown", act: AccesTechnology = AccesTechnology.UNKNOWN,
                 ):
        self.mode = mode
        """0 automatic; 1 manual; 2 force deregister; 3 set only <format> 4; manual/automatic"""
        self.format = oper_format
        """0 long format alphanumeric <oper>; 1 short format alphanumeric <oper>; 2 numeric <oper>
        Numeric format is actually just MCC+MNC (5 digits)"""
        self.operator_name = oper
        """string type, <format> indicates if the format is alphanumeric or numeric."""
        self.act = act
        """Access technology selected 0 GSM; 1 GSM Compact; 2 UTRAN; 6 UTRAN_HSDPA_HSUPA
        7 EUTRAN; 8 CDMA/HDR; 11 NR_5GCN (NR connected to 5G core Network)
        12 NGRAN (NG-RAN access technology); 13 EUTRA_NR (Dual connectivity of LTE with NR)
        The value is only relevant the moment the command is issued, it can change easily over time
        """

    def to_printable_string(self) -> str:
        """Uses COPS instance data to return a string in a format printable to a measurement file.
        
        If COPS contains the operator name directly it is given as is, if the operator name is given in numeric format,
        the name is deduced from the (mcc, mnc) pair using `get_operator_name` function

        Examples:
            >>> info = COPS(0, 0, "Free", AccesTechnology(7))
            >>> info.to_printable_string()
            >>> 'OPERATOR|Free'
            >>> info = COPS(0, 2, "20801", AccesTechnology(7))
            >>> info.to_printable_string()
            >>> 'OPERATOR|Orange'
            >>> info = COPS(0, 2, "10", AccesTechnology(7))
            >>> info.to_printable_string()
            >>> 'OPERATOR|Uknown'

        :return: String in the format 'OPERATOR|<operator_name>'
        """
        operator_name = "Unknown"
        if self.format == 0 or self.format == 1:
            if self.operator_name != "":
                operator_name = self.operator_name
        elif self.format == 2:  # Numeric format is mcc+mnc of the operator
            if len(self.operator_name) > 3:
                mcc = self.operator_name[:3]  # First 3 digits is mcc
                mnc = self.operator_name[3:]
                operator_name = self.get_operator_name(mcc, mnc)

        return f"OPERATOR|{operator_name}"

    @staticmethod
    def get_operator_name(mcc: str, mnc: str) -> str:
        """Give the name of the operator for a (mcc, mnc) couple

        Examples:
            >>> COPS.get_operator_name("208","1")
            'Orange'
            >>> COPS.get_operator_name("208","10")
            'SFR'
            >>> COPS.get_operator_name("208","3")
            'Unknown'

        :param mcc: Mobile Country Code
        :param mnc: Mobile Network Code

        :returns: Operator name as string
        """
        mcc_value = int(mcc)
        mnc_value = int(mnc)  # We need to convert it to int because mnc string can start (or not) by 0
        name = "Unknown"
        if mcc_value == 208:  # France
            if mnc_value in [1, 2]:
                name = "Orange"
            elif mnc_value in [8, 9, 10, 11, 13]:
                name = "SFR"
            elif mnc_value in [15, 16, 35, 36]:
                name = "Free"
            elif mnc_value in [20, 21, 88]:
                name = "Bouygues"

        return name

    def __bool__(self):
        """
        Evaluates to True if operator name is known
        """
        return self.operator_name != "" and self.operator_name != "Unknown"

    @classmethod
    def from_string(cls, line: str):
        """Create an instance of COPS class from the response of AT+COPS? command

        The AT+COPS? response must have the following format:
           +COPS: <mode>[,<format>,<oper>[,< AcT>]]
        If the line format is wrong, None will be returned.

        Example:
            >>> info = COPS.from_string('+COPS: 0,0,"F SFR",7')
            >>> info.to_printable_string()
            >>> 'OPERATOR|F SFR'

        :param line: line containing the main part of response of AT+COPS? command
        :return: instance of COPS class filled with data extracted from message or None if `line` format is wrong
        """
        # Remove +COPS: prefix from all lines and split values separated by ','
        # Second strip because spacing after COPS can be inconsistent
        # This requires Python 3.10
        values: list[str] = line.strip().removeprefix('+COPS:').replace('"', '').strip().split(',')
        values = [value.strip() for value in values]

        if len(values) == 1:
            print("No operator found, check network connection")
            return cls()

        if len(values) != 4:
            print(f"Incorrect COPS response format (4 values expected, {len(values)} found)")
            print(f"The COPS response was: {line}")
            return None

        try:
            return cls(mode=int(values[0]), oper_format=int(values[1]), oper=values[2],
                       act=AccesTechnology(int(values[3])))
        except ValueError:
            print(f"One of the parameters in line had incorrect format: {line}")
