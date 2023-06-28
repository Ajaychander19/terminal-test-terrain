import math

class conv:
    def freq_to_arfcn(freq) -> int:
        x = float(freq)
        arfcn = dict([(3529.92, 635328), (3530.01, 635334), (3604.80, 640320), (3604.95,640330), (3675.0, 645000), (3755.01, 650334 ) ,(3675.36, 645024), (3755, 650333), (3756.00, 650400)])
        return arfcn[x]

    def linearScale(dBm):
        milliwatt = (10 ** ((dBm) / 10))
        return milliwatt

    def dBscale(milliwatt):
        dBm = 10 * math.log10(milliwatt)
        return round(dBm, 2)
