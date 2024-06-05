# sorted_meas = {
#     (75, 1501): 1,
#     (75, 2825): 45,
#     (75, 6300): 78,
#     (82, 6300): 87,
#     (153, 1501): 10,
#     (215, 78): 36,
#     (371, 6300): 11
# }
#
# measurements = {
#     (75, 1501): (-106.7, -17.8, -68.9),
#     (153, 1501): (-108.7, -20.0, -79.5),
#     (75, 2825): (-111.7, -19.1, -83.5),
#     # (215, 78): (-104.5, -20.0, -74.4),
#     (75, 6300): (-93.6, -18.1, -67.7),
#     # (82, 6300): (-106.7, -17.8, -68.9),
#     (371, 6300): (-106.7, -17.8, -68.9)
# }
#
# columns = {couple: 5 + index for index, couple in enumerate(sorted_meas)}
# print(columns)
#
# res0 = "RSRP||||"
# print("--------------------")
#
# sorted_index_meas = list()
# for couple, meas in measurements.items():
#     sorted_index_meas.append((columns[couple], meas))
#
# print(sorted_index_meas)
# sorted_index_meas = sorted(sorted_index_meas)
#
# current_column = 5
# for (index, meas) in sorted_index_meas:
#     while index != current_column:
#         res0 += "|"
#         current_column += 1
#     res0 = res0 + "|" + str(meas[0])
#     current_column += 1
#
#
#
# print(res0)

import time
import sys

timeout = 0
while True:
    print(str(timeout))
    time.sleep(1)
    timeout += 1
    if timeout > 10:
        sys.exit("Ooof")
