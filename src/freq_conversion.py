import math

class conv:
    def freq_to_arfcn(freq) -> int:
        """Convert center frequency (MHz) to NR-ARFCN using 3GPP TS 38.101-1 Table 5.4.2.1-1.

        Replaces the hardcoded dictionary that caused KeyError for frequencies such as
        3530.0 MHz reported by the VIAVI instrument (rounded values that don't exactly
        match the 15 kHz NR-ARFCN grid entries previously in the dict).

        Frequency ranges and step sizes (3GPP TS 38.101-1):
          FR1 low  (0 - 3000 MHz):      step =  5 kHz = 0.005 MHz, N_offset=0,       F_offset=0 MHz
          FR1 high (3000 - 7125 MHz):   step = 15 kHz = 0.015 MHz, N_offset=600000,  F_offset=3000 MHz
          FR2      (24250 - 100000 MHz): step = 60 kHz = 0.060 MHz, N_offset=2016667, F_offset=24250 MHz
        """
        x = float(freq)

        if x < 3000.0:
            # FR1 low band: 0-3000 MHz, 5 kHz step
            arfcn = round(x / 0.005)
        elif x <= 7125.0:
            # FR1 high band: 3000-7125 MHz, 15 kHz step  (n78: 3530 MHz lives here)
            arfcn = round(600000 + (x - 3000.0) / 0.015)
        else:
            # FR2: 24250-100000 MHz, 60 kHz step
            arfcn = round(2016667 + (x - 24250.0) / 0.060)

        return arfcn

    def linearScale(dBm):
        milliwatt = (10 ** ((dBm) / 10))
        return milliwatt

    def dBscale(milliwatt):
        dBm = 10 * math.log10(milliwatt)
        return round(dBm, 2)
