import pandas as pd
def columns_names(filename):
    list_of_column_names = []
    viavi_file = pd.read_csv(filename, dtype=str)
    for name in viavi_file.columns:
        list_of_column_names.append(name)
    return list_of_column_names

def search_column(list, search):
    scores = {}
    for i in list:
        scores[i] = 0
    search_splited = search.split(" ")
    for i in list:
        for j in search_splited:
            if j in i:
                scores[i] = scores[i] + 1
    word_max = max(scores, key=scores.get)
    return word_max

def dic_viavi(fields, colsnames):
    dic = {}
    for f in fields:
        dic[f] = search_column(colsnames, f)
    return dic

#list_of_column_names = columns_names('test_files/fusion.csv')

#print(search_column(list_of_column_names, "S-SS RSRP"))

#print(search_column(list_of_column_names, "PCI"))

#print(search_column(list_of_column_names, "date"))
