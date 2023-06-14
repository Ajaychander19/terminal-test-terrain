class conv:
    def freq_to_arfcn(freq) -> int:
        x = int(freq)
        arfcn = dict([(3529, 635267), (3530, 635333), (3604, 640267), (3675, 645000), (3755, 650333), (3756, 650400)])
        return arfcn[x]

    def dbm_to_watt(dBm):
        watt = 10 ** ((dBm - 30) / 10)
        return watt
