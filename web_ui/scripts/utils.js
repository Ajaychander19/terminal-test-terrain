/**
 * Contains general-purpose function for program.
 * 
 * @namespace
 */
const lteBands = [
  { band: 1, earfcnMin: 0, earfcnMax: 599, nOffsDl: 0, dlFreqLow: 2110.0 },
  { band: 2, earfcnMin: 600, earfcnMax: 1199, nOffsDl: 600, dlFreqLow: 1930.0 },
  { band: 3, earfcnMin: 1200, earfcnMax: 1949, nOffsDl: 1200, dlFreqLow: 1805.0 },
  { band: 4, earfcnMin: 1950, earfcnMax: 2399, nOffsDl: 1950, dlFreqLow: 2110.0 },
  { band: 5, earfcnMin: 2400, earfcnMax: 2649, nOffsDl: 2400, dlFreqLow: 869.0 },
  { band: 6, earfcnMin: 2650, earfcnMax: 2749, nOffsDl: 2650, dlFreqLow: 875.0 },
  { band: 7, earfcnMin: 2750, earfcnMax: 3449, nOffsDl: 2750, dlFreqLow: 2620.0 },
  { band: 8, earfcnMin: 3450, earfcnMax: 3799, nOffsDl: 3450, dlFreqLow: 925.0 },
  { band: 9, earfcnMin: 3800, earfcnMax: 4149, nOffsDl: 3800, dlFreqLow: 1844.9 },
  { band: 10, earfcnMin: 4150, earfcnMax: 4749, nOffsDl: 4150, dlFreqLow: 2110.0 },
  { band: 11, earfcnMin: 4750, earfcnMax: 4949, nOffsDl: 4750, dlFreqLow: 1475.9 },
  { band: 12, earfcnMin: 5010, earfcnMax: 5179, nOffsDl: 5010, dlFreqLow: 729.0 },
  { band: 13, earfcnMin: 5180, earfcnMax: 5279, nOffsDl: 5180, dlFreqLow: 746.0 },
  { band: 14, earfcnMin: 5280, earfcnMax: 5379, nOffsDl: 5280, dlFreqLow: 758.0 },
  { band: 17, earfcnMin: 5730, earfcnMax: 5849, nOffsDl: 5730, dlFreqLow: 734.0 },
  { band: 18, earfcnMin: 5850, earfcnMax: 5999, nOffsDl: 5850, dlFreqLow: 860.0 },
  { band: 19, earfcnMin: 6000, earfcnMax: 6149, nOffsDl: 6000, dlFreqLow: 875.0 },
  { band: 20, earfcnMin: 6150, earfcnMax: 6449, nOffsDl: 6150, dlFreqLow: 791.0 },
  { band: 21, earfcnMin: 6450, earfcnMax: 6599, nOffsDl: 6450, dlFreqLow: 1495.9 },
  { band: 22, earfcnMin: 6600, earfcnMax: 7399, nOffsDl: 6600, dlFreqLow: 3510.0 },
  { band: 23, earfcnMin: 7500, earfcnMax: 7699, nOffsDl: 7500, dlFreqLow: 2180.0 },
  { band: 24, earfcnMin: 7700, earfcnMax: 8039, nOffsDl: 7700, dlFreqLow: 1525.0 },
  { band: 25, earfcnMin: 8040, earfcnMax: 8689, nOffsDl: 8040, dlFreqLow: 1930.0 },
  { band: 26, earfcnMin: 8690, earfcnMax: 9039, nOffsDl: 8690, dlFreqLow: 859.0 },
  { band: 27, earfcnMin: 9040, earfcnMax: 9209, nOffsDl: 9040, dlFreqLow: 852.0 },
  { band: 28, earfcnMin: 9210, earfcnMax: 9659, nOffsDl: 9210, dlFreqLow: 758.0 },
  { band: 29, earfcnMin: 9660, earfcnMax: 9769, nOffsDl: 9660, dlFreqLow: 717.0 },
  { band: 30, earfcnMin: 9770, earfcnMax: 9869, nOffsDl: 9770, dlFreqLow: 2350.0 },
  { band: 31, earfcnMin: 9870, earfcnMax: 9919, nOffsDl: 9870, dlFreqLow: 462.5 },
  { band: 32, earfcnMin: 9920, earfcnMax: 10359, nOffsDl: 9920, dlFreqLow: 1452.0 },
  { band: 33, earfcnMin: 36000, earfcnMax: 36199, nOffsDl: 36000, dlFreqLow: 1900.0 },
  { band: 34, earfcnMin: 36200, earfcnMax: 36349, nOffsDl: 36200, dlFreqLow: 2010.0 },
  { band: 35, earfcnMin: 36350, earfcnMax: 36949, nOffsDl: 36350, dlFreqLow: 1850.0 },
  { band: 36, earfcnMin: 36950, earfcnMax: 37549, nOffsDl: 36950, dlFreqLow: 1930.0 },
  { band: 37, earfcnMin: 37550, earfcnMax: 37749, nOffsDl: 37550, dlFreqLow: 1910.0 },
  { band: 38, earfcnMin: 37750, earfcnMax: 38249, nOffsDl: 37750, dlFreqLow: 2570.0 },
  { band: 39, earfcnMin: 38250, earfcnMax: 38649, nOffsDl: 38250, dlFreqLow: 1880.0 },
  { band: 40, earfcnMin: 38650, earfcnMax: 39649, nOffsDl: 38650, dlFreqLow: 2300.0 },
  { band: 41, earfcnMin: 39650, earfcnMax: 41589, nOffsDl: 39650, dlFreqLow: 2496.0 },
  { band: 42, earfcnMin: 41590, earfcnMax: 43589, nOffsDl: 41590, dlFreqLow: 3400.0 },
  { band: 43, earfcnMin: 43590, earfcnMax: 45589, nOffsDl: 43590, dlFreqLow: 3600.0 },
  { band: 44, earfcnMin: 45590, earfcnMax: 46589, nOffsDl: 45590, dlFreqLow: 703.0 },
  { band: 45, earfcnMin: 46590, earfcnMax: 46789, nOffsDl: 46590, dlFreqLow: 1447.0 },
  { band: 46, earfcnMin: 46790, earfcnMax: 54539, nOffsDl: 46790, dlFreqLow: 5150.0 },
  { band: 47, earfcnMin: 54540, earfcnMax: 55239, nOffsDl: 54540, dlFreqLow: 5855.0 },
  { band: 48, earfcnMin: 55240, earfcnMax: 56739, nOffsDl: 55240, dlFreqLow: 3550.0 },
  { band: 49, earfcnMin: 56740, earfcnMax: 58239, nOffsDl: 56740, dlFreqLow: 3550.0 },
  { band: 50, earfcnMin: 58240, earfcnMax: 59089, nOffsDl: 58240, dlFreqLow: 1432.0 },
  { band: 51, earfcnMin: 59090, earfcnMax: 59139, nOffsDl: 59090, dlFreqLow: 1427.0 },
  { band: 52, earfcnMin: 59140, earfcnMax: 60139, nOffsDl: 59140, dlFreqLow: 3300.0 },
  { band: 53, earfcnMin: 60140, earfcnMax: 60254, nOffsDl: 60140, dlFreqLow: 2483.5 },
  { band: 54, earfcnMin: 60255, earfcnMax: 60304, nOffsDl: 60255, dlFreqLow: 1670.0 },
  { band: 65, earfcnMin: 65536, earfcnMax: 66435, nOffsDl: 65536, dlFreqLow: 2110.0 },
  { band: 66, earfcnMin: 66436, earfcnMax: 67335, nOffsDl: 66436, dlFreqLow: 2110.0 },
  { band: 67, earfcnMin: 67336, earfcnMax: 67535, nOffsDl: 67336, dlFreqLow: 738.0 },
  { band: 68, earfcnMin: 67536, earfcnMax: 67835, nOffsDl: 67536, dlFreqLow: 753.0 },
  { band: 69, earfcnMin: 67836, earfcnMax: 68335, nOffsDl: 67836, dlFreqLow: 2570.0 },
  { band: 70, earfcnMin: 68336, earfcnMax: 68585, nOffsDl: 68336, dlFreqLow: 1995.0 },
  { band: 71, earfcnMin: 68586, earfcnMax: 68935, nOffsDl: 68586, dlFreqLow: 617.0 },
  { band: 72, earfcnMin: 68936, earfcnMax: 68985, nOffsDl: 68936, dlFreqLow: 461.0 },
  { band: 73, earfcnMin: 68986, earfcnMax: 69035, nOffsDl: 68986, dlFreqLow: 460.0 },
  { band: 74, earfcnMin: 69036, earfcnMax: 69465, nOffsDl: 69036, dlFreqLow: 1475.0 },
  { band: 75, earfcnMin: 69466, earfcnMax: 70315, nOffsDl: 69466, dlFreqLow: 1432.0 },
  { band: 76, earfcnMin: 70316, earfcnMax: 70365, nOffsDl: 70316, dlFreqLow: 1427.0 },
  { band: 85, earfcnMin: 70366, earfcnMax: 70545, nOffsDl: 70366, dlFreqLow: 728.0 },
  { band: 87, earfcnMin: 70546, earfcnMax: 70595, nOffsDl: 70546, dlFreqLow: 420.0 },
  { band: 88, earfcnMin: 70596, earfcnMax: 70645, nOffsDl: 70596, dlFreqLow: 422.0 },
  { band: 103, earfcnMin: 70646, earfcnMax: 70655, nOffsDl: 70646, dlFreqLow: 757.0 },
  { band: 106, earfcnMin: 70656, earfcnMax: 70705, nOffsDl: 70656, dlFreqLow: 935.0 },
  { band: 107, earfcnMin: 70706, earfcnMax: 71055, nOffsDl: 70706, dlFreqLow: 612.0 },
  { band: 108, earfcnMin: 71056, earfcnMax: 73335, nOffsDl: 71056, dlFreqLow: 470.0 },
  { band: 111, earfcnMin: 73386, earfcnMax: 73485, nOffsDl: 73386, dlFreqLow: 1820.0 }
];
const nrBands = [
  // FR1 bands (sub-6 GHz)
  { band: 'n1', duplexMode: 'FDD', commonName: 'IMT', uplink: { low: 1920, high: 1980 }, downlink: { low: 2110, high: 2170 }, duplexSpacing: 190, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 45, 50] },
  { band: 'n2', duplexMode: 'FDD', commonName: 'PCS', uplink: { low: 1850, high: 1910 }, downlink: { low: 1930, high: 1990 }, duplexSpacing: 80, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 45, 50] },
  { band: 'n3', duplexMode: 'FDD', commonName: 'DCS', uplink: { low: 1710, high: 1785 }, downlink: { low: 1805, high: 1880 }, duplexSpacing: 95, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 45, 50] },
  { band: 'n5', duplexMode: 'FDD', commonName: 'CLR', uplink: { low: 824, high: 849 }, downlink: { low: 869, high: 894 }, duplexSpacing: 45, channelBandwidths: [5, 10, 15, 20, 25] },
  { band: 'n7', duplexMode: 'FDD', commonName: 'IMT-E', uplink: { low: 2500, high: 2570 }, downlink: { low: 2620, high: 2690 }, duplexSpacing: 120, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 45, 50] },
  { band: 'n8', duplexMode: 'FDD', commonName: 'Extended GSM', uplink: { low: 880, high: 915 }, downlink: { low: 925, high: 960 }, duplexSpacing: 45, channelBandwidths: [5, 10, 15, 20, 25] },
  { band: 'n12', duplexMode: 'FDD', commonName: 'Lower SMH', uplink: { low: 699, high: 716 }, downlink: { low: 729, high: 746 }, duplexSpacing: 30, channelBandwidths: [5, 10, 15] },
  { band: 'n13', duplexMode: 'FDD', commonName: 'Upper SMH', uplink: { low: 777, high: 787 }, downlink: { low: 746, high: 756 }, duplexSpacing: -31, channelBandwidths: [5, 10] },
  { band: 'n14', duplexMode: 'FDD', commonName: 'Upper SMH', uplink: { low: 788, high: 798 }, downlink: { low: 758, high: 768 }, duplexSpacing: -30, channelBandwidths: [5, 10] },
  { band: 'n18', duplexMode: 'FDD', commonName: 'Lower 800', uplink: { low: 815, high: 830 }, downlink: { low: 860, high: 875 }, duplexSpacing: 45, channelBandwidths: [5, 10, 15] },
  { band: 'n20', duplexMode: 'FDD', commonName: 'Digital Dividend', uplink: { low: 832, high: 862 }, downlink: { low: 791, high: 821 }, duplexSpacing: -41, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n24', duplexMode: 'FDD', commonName: 'Upper L-band', uplink: { low: 1626.5, high: 1660.5 }, downlink: { low: 1525, high: 1559 }, duplexSpacing: -101.5, channelBandwidths: [5, 10] },
  { band: 'n25', duplexMode: 'FDD', commonName: 'Extended PCS', uplink: { low: 1850, high: 1915 }, downlink: { low: 1930, high: 1995 }, duplexSpacing: 80, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 45, 50] },
  { band: 'n26', duplexMode: 'FDD', commonName: 'Extended CLR', uplink: { low: 814, high: 849 }, downlink: { low: 859, high: 894 }, duplexSpacing: 45, channelBandwidths: [3, 5, 10, 15, 20] },
  { band: 'n28', duplexMode: 'FDD', commonName: 'APT', uplink: { low: 703, high: 748 }, downlink: { low: 758, high: 803 }, duplexSpacing: 55, channelBandwidths: [5, 10, 15, 20, 25] },
  { band: 'n29', duplexMode: 'SDL', commonName: 'Lower SMH', uplink: { low: null, high: null }, downlink: { low: 717, high: 728 }, duplexSpacing: null, channelBandwidths: [5, 10] },
  { band: 'n30', duplexMode: 'FDD', commonName: 'WCS', uplink: { low: 2305, high: 2315 }, downlink: { low: 2350, high: 2360 }, duplexSpacing: 45, channelBandwidths: [5, 10] },
  { band: 'n31', duplexMode: 'FDD', commonName: 'NMT', uplink: { low: 452.5, high: 457.5 }, downlink: { low: 462.5, high: 467.5 }, duplexSpacing: 10, channelBandwidths: [3, 5] },
  { band: 'n34', duplexMode: 'TDD', commonName: 'IMT', uplink: { low: 2010, high: 2025 }, downlink: { low: 2010, high: 2025 }, duplexSpacing: null, channelBandwidths: [5, 10, 15] },
  { band: 'n38', duplexMode: 'TDD', commonName: 'IMT-E', uplink: { low: 2570, high: 2620 }, downlink: { low: 2570, high: 2620 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50] },
  { band: 'n39', duplexMode: 'TDD', commonName: 'DCS-IMT Gap', uplink: { low: 1880, high: 1920 }, downlink: { low: 1880, high: 1920 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40] },
  { band: 'n40', duplexMode: 'TDD', commonName: 'S-Band', uplink: { low: 2300, high: 2400 }, downlink: { low: 2300, high: 2400 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n41', duplexMode: 'TDD', commonName: 'BRS', uplink: { low: 2496, high: 2690 }, downlink: { low: 2496, high: 2690 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n46', duplexMode: 'TDD', commonName: 'U-NII 5-8', uplink: { low: 5150, high: 5925 }, downlink: { low: 5150, high: 5925 }, duplexSpacing: null, channelBandwidths: [20, 40, 60, 80, 100] },
  { band: 'n47', duplexMode: 'TDD', commonName: 'U-NII 5-8', uplink: { low: 5855, high: 5925 }, downlink: { low: 5855, high: 5925 }, duplexSpacing: null, channelBandwidths: [20, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n48', duplexMode: 'TDD', commonName: 'CBRS', uplink: { low: 3550, high: 3700 }, downlink: { low: 3550, high: 3700 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n50', duplexMode: 'TDD', commonName: 'L-Band', uplink: { low: 1432, high: 1517 }, downlink: { low: 1432, high: 1517 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50, 60, 80] },
  { band: 'n51', duplexMode: 'TDD', commonName: 'L-Band Extension', uplink: { low: 1427, high: 1432 }, downlink: { low: 1427, high: 1432 }, duplexSpacing: null, channelBandwidths: [5] },
  { band: 'n53', duplexMode: 'TDD', commonName: 'S-Band', uplink: { low: 2483.5, high: 2495 }, downlink: { low: 2483.5, high: 2495 }, duplexSpacing: null, channelBandwidths: [5, 10] },
  { band: 'n54', duplexMode: 'TDD', commonName: 'L-band', uplink: { low: 1670, high: 1675 }, downlink: { low: 1670, high: 1675 }, duplexSpacing: null, channelBandwidths: [5] },
  { band: 'n65', duplexMode: 'FDD', commonName: 'Extended IMT', uplink: { low: 1920, high: 1980 }, downlink: { low: 2110, high: 2170 }, duplexSpacing: 190, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 45, 50] },
  { band: 'n66', duplexMode: 'FDD', commonName: 'Extended AWS', uplink: { low: 1710, high: 1780 }, downlink: { low: 2110, high: 2200 }, duplexSpacing: 400, channelBandwidths: [5, 10, 15, 20, 25, 30, 35, 40, 45] },
  { band: 'n67', duplexMode: 'SDL', commonName: 'EU 700', uplink: { low: null, high: null }, downlink: { low: 738, high: 758 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n70', duplexMode: 'FDD', commonName: 'Supplementary AWS', uplink: { low: 1695, high: 1710 }, downlink: { low: 1995, high: 2020 }, duplexSpacing: 300, channelBandwidths: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50] },
  { band: 'n71', duplexMode: 'FDD', commonName: 'Digital Dividend', uplink: { low: 663, high: 698 }, downlink: { low: 617, high: 652 }, duplexSpacing: -46, channelBandwidths: [5, 10, 15, 20, 25, 30, 35] },
  { band: 'n72', duplexMode: 'FDD', commonName: 'PMR', uplink: { low: 451, high: 456 }, downlink: { low: 461, high: 466 }, duplexSpacing: 10, channelBandwidths: [3, 5] },
  { band: 'n74', duplexMode: 'FDD', commonName: 'Lower L-Band', uplink: { low: 1427, high: 1470 }, downlink: { low: 1475, high: 1518 }, duplexSpacing: 48, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n75', duplexMode: 'SDL', commonName: 'L-Band', uplink: { low: null, high: null }, downlink: { low: 1432, high: 1517 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50] },
  { band: 'n76', duplexMode: 'SDL', commonName: 'L-Band Extension', uplink: { low: null, high: null }, downlink: { low: 1427, high: 1432 }, duplexSpacing: null, channelBandwidths: [5] },
  { band: 'n77', duplexMode: 'TDD', commonName: 'C-Band', uplink: { low: 3300, high: 4200 }, downlink: { low: 3300, high: 4200 }, duplexSpacing: null, channelBandwidths: [10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n78', duplexMode: 'TDD', commonName: 'C-Band', uplink: { low: 3300, high: 3800 }, downlink: { low: 3300, high: 3800 }, duplexSpacing: null, channelBandwidths: [10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n79', duplexMode: 'TDD', commonName: 'C-Band', uplink: { low: 4400, high: 5000 }, downlink: { low: 4400, high: 5000 }, duplexSpacing: null, channelBandwidths: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n80', duplexMode: 'SUL', commonName: 'DCS', uplink: { low: 1710, high: 1785 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40] },
  { band: 'n81', duplexMode: 'SUL', commonName: 'Extended GSM', uplink: { low: 880, high: 915 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n82', duplexMode: 'SUL', commonName: 'Digital Dividend', uplink: { low: 832, high: 862 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n83', duplexMode: 'SUL', commonName: 'APT', uplink: { low: 703, high: 748 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30] },
  { band: 'n84', duplexMode: 'SUL', commonName: 'IMT', uplink: { low: 1920, high: 1980 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50] },
  { band: 'n85', duplexMode: 'FDD', commonName: 'Extended Lower SMH', uplink: { low: 698, high: 716 }, downlink: { low: 728, high: 746 }, duplexSpacing: 30, channelBandwidths: [3, 5, 10, 15] },
  { band: 'n86', duplexMode: 'SUL', commonName: 'Extended AWS', uplink: { low: 1710, high: 1780 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 40] },
  { band: 'n89', duplexMode: 'SUL', commonName: 'CLR', uplink: { low: 824, high: 849 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n90', duplexMode: 'TDD', commonName: 'BRS', uplink: { low: 2496, high: 2690 }, downlink: { low: 2496, high: 2690 }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 45, 50, 60, 70, 80, 90, 100] },
  { band: 'n91', duplexMode: 'FDD', commonName: 'DD L-Band', uplink: { low: 832, high: 862 }, downlink: { low: 1427, high: 1432 }, duplexSpacing: 595, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n92', duplexMode: 'FDD', commonName: 'DD L-Band', uplink: { low: 832, high: 862 }, downlink: { low: 1432, high: 1517 }, duplexSpacing: 600, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n93', duplexMode: 'FDD', commonName: 'Extended GSM L-Band', uplink: { low: 880, high: 915 }, downlink: { low: 1427, high: 1432 }, duplexSpacing: 547, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n94', duplexMode: 'FDD', commonName: 'Extended GSM L-Band', uplink: { low: 880, high: 915 }, downlink: { low: 1432, high: 1517 }, duplexSpacing: 532, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n95', duplexMode: 'SUL', commonName: 'IMT', uplink: { low: 2010, high: 2025 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20] },
  { band: 'n96', duplexMode: 'TDD', commonName: 'U-NII 5-8', uplink: { low: 5925, high: 7125 }, downlink: { low: 5925, high: 7125 }, duplexSpacing: null, channelBandwidths: [20, 40, 60, 80, 100] },
  { band: 'n97', duplexMode: 'SUL', commonName: 'S-Band', uplink: { low: 2300, high: 2400 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n98', duplexMode: 'SUL', commonName: 'DCS-IMT Gap', uplink: { low: 1880, high: 1920 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10, 15, 20, 25, 30, 40] },
  { band: 'n99', duplexMode: 'SUL', commonName: 'Upper L-band', uplink: { low: 1626.5, high: 1660.5 }, downlink: { low: null, high: null }, duplexSpacing: null, channelBandwidths: [5, 10] },
  { band: 'n100', duplexMode: 'FDD', commonName: 'GSM-R', uplink: { low: 874.4, high: 880 }, downlink: { low: 919.4, high: 925 }, duplexSpacing: 45, channelBandwidths: [3, 5] },
  { band: 'n101', duplexMode: 'FDD', commonName: 'FRMCS', uplink: { low: 1900, high: 1910 }, downlink: { low: 1900, high: 1910 }, duplexSpacing: null, channelBandwidths: [5, 10] },
  { band: 'n102', duplexMode: 'TDD', commonName: 'U-NII-5', uplink: { low: 5925, high: 6425 }, downlink: { low: 5925, high: 6425 }, duplexSpacing: null, channelBandwidths: [20, 40, 60, 80, 100] },
  { band: 'n104', duplexMode: 'TDD', commonName: 'U-NII-6-8', uplink: { low: 6425, high: 7125 }, downlink: { low: 6425, high: 7125 }, duplexSpacing: null, channelBandwidths: [20, 30, 40, 50, 60, 70, 80, 90, 100] },
  { band: 'n105', duplexMode: 'FDD', commonName: 'Digital Dividend', uplink: { low: 663, high: 703 }, downlink: { low: 612, high: 652 }, duplexSpacing: -51, channelBandwidths: [5, 10, 15, 20, 25, 30, 35] },
  { band: 'n106', duplexMode: 'FDD', commonName: 'LMRS', uplink: { low: 896, high: 901 }, downlink: { low: 935, high: 940 }, duplexSpacing: 39, channelBandwidths: [3] },

  // FR2 bands (mmWave)
  { band: 'n257', duplexMode: 'TDD', commonName: '28 GHz', uplink: { low: 26500, high: 29500 }, downlink: { low: 26500, high: 29500 }, duplexSpacing: null, channelBandwidths: [50, 100, 200, 400] },
  { band: 'n258', duplexMode: 'TDD', commonName: '26 GHz', uplink: { low: 24250, high: 27500 }, downlink: { low: 24250, high: 27500 }, duplexSpacing: null, channelBandwidths: [50, 100, 200, 400] },
  { band: 'n259', duplexMode: 'TDD', commonName: '39 GHz', uplink: { low: 37000, high: 40000 }, downlink: { low: 37000, high: 40000 }, duplexSpacing: null, channelBandwidths: [50, 100, 200, 400] },
  { band: 'n260', duplexMode: 'TDD', commonName: '39 GHz', uplink: { low: 37000, high: 40000 }, downlink: { low: 37000, high: 40000 }, duplexSpacing: null, channelBandwidths: [50, 100, 200, 400] },
  { band: 'n261', duplexMode: 'TDD', commonName: '28 GHz', uplink: { low: 27500, high: 28350 }, downlink: { low: 27500, high: 28350 }, duplexSpacing: null, channelBandwidths: [50, 100, 200, 400] },
  { band: 'n262', duplexMode: 'TDD', commonName: '47 GHz', uplink: { low: 47200, high: 48200 }, downlink: { low: 47200, high: 48200 }, duplexSpacing: null, channelBandwidths: [50, 100, 200, 400] },
  { band: 'n263', duplexMode: 'TDD', commonName: '60 GHz', uplink: { low: 57000, high: 71000 }, downlink: { low: 57000, high: 71000 }, duplexSpacing: null, channelBandwidths: [50, 100, 200, 400] }
];

const nrArfcnParameters = [
  { freqRange: { low: 0, high: 3000 }, deltaFGlobal: 5, fRefOffs: 0, nRefOffs: 0 },
  { freqRange: { low: 3000, high: 24250 }, deltaFGlobal: 15, fRefOffs: 3000, nRefOffs: 600000 },
  { freqRange: { low: 24250, high: 100000 }, deltaFGlobal: 60, fRefOffs: 24250.08, nRefOffs: 2016667 }
];



const utils = {
    normalize: function(val, min, max) {
        // Clamp et normalisation
        return Math.min(Math.max((val - min) / (max - min), 0), 1);
    },

    getColorFromPalette: function(val, min, max, palette) {
        const normalized = utils.normalize(val, min, max);
        // Calcul de l'index dans la palette
        const idx = Math.floor(normalized * (palette.length - 1));
        return palette[idx];
    },

    /**
     * Calculates the direction 
     * @param {number} angle the azimuth value
     * @returns {number} Azimuth in direction (N, W, S, ...)
     */
    getCardinalDirection :function (angle) {
        const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        const index = Math.round(angle / 45) % 8;
        return directions[index];
    },

    
    /**
     * Calculates the azimuth (initial bearing) between two GPS points in degrees.
     * @param {number} lat1 Latitude of the starting point
     * @param {number} lon1 Longitude of the starting point
     * @param {number} lat2 Latitude of the destination point
     * @param {number} lon2 Longitude of the destination point
     * @returns {number} Azimuth in degrees (0° = North, 90° = East)
     */
    /*calculateAzimuth: function(lat1, lon1, lat2, lon2) {
        return getGreatCircleBearing(
            { latitude: lat1, longitude: lon1 },
            { latitude: lat2, longitude: lon2 }
        );
    },*/
    // Fonction pour convertir les degrés en radians
    toRadians: function (degrees) {
        return degrees * (Math.PI / 180);
    },

    // Fonction pour convertir les radians en degrés
    toDegrees: function (radians) {
        return radians * (180 / Math.PI);
    },

    // Fonction de calcul de l'azimut
    calculateAzimuth: function (lat1, lon1, lat2, lon2) {
        const start = { latitude: lat1, longitude: lon1 };
        const end = { latitude: lat2, longitude: lon2 };
        return this.getGreatCircleBearing(start, end);
    },

    // Fonction de calcul du cap (bearing) du grand cercle
    getGreatCircleBearing: function (start, end) {
        const φ1 = this.toRadians(start.latitude);
        const φ2 = this.toRadians(end.latitude);
        const Δλ = this.toRadians(end.longitude - start.longitude);

        const y = Math.sin(Δλ) * Math.cos(φ2);
        const x =
        Math.cos(φ1) * Math.sin(φ2) -
        Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
        const θ = Math.atan2(y, x);

        return (this.toDegrees(θ) + 360) % 360;
    },

    beamToDirection: function(beamNumber, totalBeams = 8) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        if (isNaN(beamNumber) || totalBeams <= 0) return '-';

        let angle = (360 / totalBeams) * beamNumber;

        return directions[Math.round(angle / 45) % 8];
    },

    /**
     * search for the band corresponding to a given earfcn
     * @param earfcn earfcn
     * @returns the corresponding frequency (Mhz)
    */
    earfcnToFreqLte: function(earfcn) {
        for (let band of lteBands) {
            if (earfcn >= band.earfcnMin && earfcn <= band.earfcnMax) {
            return band.dlFreqLow + 0.1 * (earfcn - band.nOffsDl);
            }
        }
        return null; // EARFCN not found
    },

    nrarfcnToFreq5G: function (nrarfcn) {
        for (let params of nrArfcnParameters) {
            const { freqRange, deltaFGlobal, fRefOffs, nRefOffs } = params;
            const fRef = fRefOffs + (deltaFGlobal / 1000) * (nrarfcn - nRefOffs);
            if (fRef >= freqRange.low && fRef <= freqRange.high) {
            return fRef;
            }
        }
        return null; // NR-ARFCN not found
    },

   tofreq: function(nrarfcn, mode) {
        console.log("used technology in tofreq is : ", mode);

        if (!mode) return null;
        let techno = Array.isArray(mode) ? mode.at(-1) : mode;

        if (techno === "4G") {
            for (const band of lteBands) {
                if (nrarfcn >= band.earfcnMin && nrarfcn <= band.earfcnMax) {
                    return band.dlFreqLow + 0.1 * (nrarfcn - band.nOffsDl);
                }
            }
        } 
        else if (techno === "5G" || techno === "5G NR") {
            for (const params of nrArfcnParameters) {
                const { freqRange, deltaFGlobal, fRefOffs, nRefOffs } = params;
                const fRef = fRefOffs + (deltaFGlobal / 1000) * (nrarfcn - nRefOffs);
                if (fRef >= freqRange.low && fRef <= freqRange.high) {
                    return fRef;
                }
            }
        }

        return null;
    },



    
    /**
     * Deep-copies an object (copy of the object and its childs), 
     * by serializing it in JSON then decoding this JSON.
     * 
     * @param {*} obj Object to deep-copy.
     * @returns A deep-copy of obj.
     * 
     * @function
     */
    deepCopy: function (obj) { return JSON.parse(JSON.stringify(obj)); },

    /**
     * Finds the indexes of occurences of a given value in an array.
     * 
     * @param {Array} arr Array to search in. 
     * @param {*} obj Object to search. 
     * @returns An Array of indexes of obj occurences.
     * 
     * @function
     */
    indexesOf: function (arr, obj) {

        let result = [];
        for (let i in arr) if (obj === arr[i]) result.push(parseInt(i));
        return result;

    },

    /**
     * Searches an EARFCN and PCI pair amongs EARFCN / PCI lists.
     * 
     * @param {Array} earfcns EARFCN list to search in.
     * @param {Array} pcis PCI list to search in.
     * @param {number} earfcn EARFCN to search.
     * @param {number} pci PCI to search.
     * @returns The index of the pair in earfcns and pcis if found, -1 otherwise.
     * 
     * @function
     */
    indexOfEarpci: function (earfcns, pcis, earfcn, pci) {

        let earfcnIdx = utils.indexesOf(earfcns, earfcn);
        let pcisIdx = utils.indexesOf(pcis, pci);

        let inter = earfcnIdx.filter((e) => pcisIdx.includes(e))

        return inter.length !== 0 ? inter[0] : -1;

    },

    /**
     * Remove an EARFCN / PCI pair from lists of EARFCN / PCI.
     * 
     * @param {Array} earfcns EARFCN list.
     * @param {Array} pcis PCI list.
     * @param {number} earfcn EARFCN to remove from list.
     * @param {number} pci PCI to remove from list.
     * 
     * @function
     */
    removeEarpci: function (earfcns, pcis, earfcn, pci) {
        
        let i = utils.indexOfEarpci(earfcns, pcis, earfcn, pci);

        if (i !== -1) {
            earfcns.splice(i, 1);
            pcis.splice(i, 1);
        }

    },

    /**
     * Filters EARFCN / PCIS from a superset list, using a subset list.
     * 
     * @param {Array} earfcns Superset of EARFCNs 
     * @param {Array} pcis Superset of PCIs
     * @param {Array} beams Superset of Beams
     * @param {Array} reqEarfcns Subset of EARFCNs (if null, represents all EARFCNs from the superset).
     * @param {Array} reqPcis Subset of PCIs (if null, represents all PCIs from the superset).
     * @param {Array} reqBeams Subset of Beams
     * @returns Object which contains lists of filtered EARFCNs / PCIs, and list of indexes of EARFCNs / PCIs
     * pairs in the superset.
     * 
     * @function 
     */
    subEarpci: function(earfcns, pcis, beams = null, reqEarfcns = null, reqPcis = null, reqBeams = null) {
    let result = { earfcns: [], pcis: [], beams: {}, indices: [] };

    if (!beams) beams = [];

    // Convertir les filtres en Set pour lookup rapide
    let reqEarfcnsSet = reqEarfcns ? new Set(reqEarfcns) : null;
    let reqPcisSet = reqPcis ? new Set(reqPcis) : null;

    // Déterminer les indices à considérer
    let subEarfcnsIdx = reqEarfcns ? earfcns.map((val, i) => reqEarfcnsSet.has(val) ? i : -1).filter(i => i !== -1)
                                   : earfcns.map((_, i) => i);
    let subPcisIdx = reqPcis ? pcis.map((val, i) => reqPcisSet.has(val) ? i : -1).filter(i => i !== -1)
                             : pcis.map((_, i) => i);

    // Utiliser un Set pour éviter duplication des clés (earfcn_pci)
    let seenKeys = new Set();

    subEarfcnsIdx.forEach(i => {
        let e = earfcns[i];
        let p = pcis[i];

        // Vérifier si l'indice est également dans subPcisIdx
        if (!subPcisIdx.includes(i)) return;

        // Vérifier si la paire e/p correspond aux beams requis
        if (reqBeams && beams[i] !== undefined) {
            let beamAllowed = Array.isArray(reqBeams[p]) 
                              ? reqBeams[p].includes("all") || reqBeams[p].includes(beams[i].toString())
                              : true;
            if (!beamAllowed) return;
        }

        // Clé unique pour éviter duplication
        let key = `${e}_${p}`;
        if (seenKeys.has(key)) return;
        seenKeys.add(key);

        // Ajouter les résultats
        result.earfcns.push(e);
        result.pcis.push(p);
        result.indices.push(i);

        // Ajouter les beams
        if (beams[i] !== undefined) {
            if (!result.beams[p]) result.beams[p] = [];
            if (!result.beams[p].includes(beams[i])) result.beams[p].push(beams[i]);
        }
    });

    // Fallback : seulement si aucun filtre n’est appliqué
    if (result.earfcns.length === 0 && !reqEarfcns && !reqPcis && !reqBeams) {
        for (let i = 0; i < earfcns.length; i++) {
            let key = `${earfcns[i]}_${pcis[i]}`;
            if (!seenKeys.has(key)) {
                seenKeys.add(key);
                result.earfcns.push(earfcns[i]);
                result.pcis.push(pcis[i]);
                result.indices.push(i);
                if (beams[i] !== undefined) {
                    if (!result.beams[pcis[i]]) result.beams[pcis[i]] = [];
                    if (!result.beams[pcis[i]].includes(beams[i])) result.beams[pcis[i]].push(beams[i]);
                }
            }
        }
    }

    return result;
},





    /**
     * Pushes elements of arrayB in arrayA if not already in arrayA.
     * 
     * @param {Array} arrayA Array where arrayB elements will be inserted.
     * @param {Array} arrayB Array of elements to be inserted into arrayA.
     */
    interPush: function (arrayA, arrayB) {
        arrayB.forEach(
            (elt) => { if (!arrayA.includes(elt)) arrayA.push(elt); }
        )
    }

}