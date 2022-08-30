import os
from messages import *
from PhoneId import*
from traceMap import*
from os import path
import socketserver
import sys
import webbrowser
import http.server


def createSite_json(listfiles,directory):
    """Creates CSV files, each dedicated to an operator, that contains information about the operator's base station,
    such as administrative identifiers, geolocation data... and JSON zoning files, also each dedicated to an operator,
    that describes partitioning of these sites.
    These files are produced from two files, provided by Cartoradio :
        - Antennes_Emetteurs_Bandes_Cartoradio.csv, which contains information about base station
        such as operator name, administrative identifiers, or emitting frequencies.
        - Sites_Cartoradio.csv, which contains information about base station such as address, geolocation,
        and owers of the place where base stations are.

    Parameters:
        listfiles : list of selected files.
        directory : working directory path.
    """

    # Reading files...
    df0 = pd.read_csv(listfiles[0],sep=';',encoding='ISO-8859-1')
    df1 = pd.read_csv(listfiles[1],sep=';',encoding='ISO-8859-1')

    # Identifying files and joining them with support numbers field.
    if (df0.shape[0]>df1.shape[0]):
        df1.set_index("Numéro du support", inplace=True)
        res=df0.join(df1, on='Numéro de support',how='left')
    else:
        df0.set_index("Numéro du support", inplace=True)
        res = df1.join(df0, on='Numéro de support', how='left')

    # Creating JSON data based on the previous join between data from files.
    # No duplicates.
    Antennas = pd.DataFrame(
        {
            "Numero du support": res["Numéro de support"], "Numero Cartoradio": res["Numéro Cartoradio"],
            "Azimut": res["Azimut"], "Exploitant": res["Exploitant"],
            "Systeme": res["Système"],"Longitude":res["Longitude"],"Latitude": res["Latitude"],"azimutMin": 0,
            "azimutMax": 0, "Hauteur / sol": res["Hauteur / sol"]
        }
    ).drop_duplicates()

    # Grouping JSON data by antennas operators.
    operators=Antennas.groupby(["Exploitant"])
    operatorNames=["BOUYGUES TELECOM","FREE MOBILE","ORANGE","SFR"]

    # Creating dedicated files to each operator.
    for oper in operators.groups.keys():
        if oper in operatorNames:
            site_zone, carte, rejected = createSitefiles(operators, oper)

            # Producing site CSV file.
            carte.to_csv(directory+"/sites" + "_" + oper + ".csv", sep='\t', encoding='ISO-8859-1')

            # Producing JSON site zone file.
            with open(directory+"/sites" + "_" + oper + "_" + "Zone" + ".json", 'w') as outfile:
                json.dump(site_zone, outfile, indent=4, separators=(',', ': '), sort_keys=False)

            # Producing excluded base station JSON file.
            with open("{}/rejected_{}.json".format(directory, oper), "w") as rejected_file:
                json.dump(rejected, rejected_file, indent=4, separators=(',', ': '), sort_keys=False)

def Associate_cell(listfiles,directory):
    """Produces association JSON file, which contains cells information, from the Zk JSON file
    data and the CSV site file.

    Cells of the association file are produced with the Scipy's implementation of the Voronoi algorithm.

    Parameters:
        listfile: list which contains the two files to read.
        directory: directory where the association JSON will be produced.

    Returns:
        The calculated cells list if the operation succeed, "ERROR" otherwise.
    """
    lteTable=pd.DataFrame()
    TACtable=pd.DataFrame()
    carte = pd.DataFrame()
    filename=""

    # Reading input files.
    for file in listfiles:

        # Site file case.
        if getfileName(file).split("_")[0] == "sites":
            filename=getfileName(file.split("_")[1])
            df=pd.read_csv(file,sep='\t', encoding="ISO-8859-1")
            carte = pd.DataFrame(
                {"Numero Cartoradio": df["Numero Cartoradio"], "Azimut": df["Azimut"], "Systeme": df["Systeme"],
                 "Longitude": df["Longitude"], "Latitude": df["Latitude"], "azimutMin": df["azimutMin"], "azimutMax": df["azimutMax"]})
        else:   # JSON Zk case
            json_objects = None

            # Opening JSON Zk file.
            with open(file) as json_data:
                json_objects = json.load(json_data)

            # Reading data.
            for item in json_objects:

                first_key = list(item.keys())[0]

                # Processing LTE OTA data.
                if (first_key == "SIB"):
                    coord = geometry.Point(
                        float(item["SIB"]["geolocation"]["lat"]),
                        float(item["SIB"]["geolocation"]["lng"]))
                    df=pd.DataFrame({"TAC": [item["SIB"]["TAC"]], "CellID": [item["SIB"]["CellID"]],
                                     "PCI": [item["SIB"]["PCI"]], "EARFCN": [item["SIB"]["EARFCN"]],
                                     "geolocation": [coord],"mcc":[item["SIB"]["mcc"]],"mnc":[item["SIB"]["mnc"]]})
                    TACtable=TACtable.append(df,sort=False,ignore_index=True)
                elif (list(item.keys())[0] == "Mesurement"):    # Processing LTEPhone data otherwise.
                    coord = geometry.Point(
                        float(item["Mesurement"]["Geolocation"]["lat"]),
                        float(item["Mesurement"]["Geolocation"]["lng"]))
                    df=pd.DataFrame({"PCI": [item["Mesurement"]["PCI"]], "EARFCN": [item["Mesurement"]["EARFCN"]],
                                     "Geolocation": [coord],"RSRP":[item["Mesurement"]["RSRP"]],"neighbourMax_RSRP":[item["Mesurement"]["neighbourMax_RSRP"]]})
                    lteTable=lteTable.append(df,sort=False,ignore_index=True)

    print("reading done")
    pciEarfcnTable =lteTable.groupby(["PCI", "EARFCN"], as_index=False)
    cellList=cellInfo(TACtable, pciEarfcnTable, carte)  # Calculating cells.
    if cellList!="ERROR":
        with open(os.path.join(directory,filename + "_association.json"), 'w') as outfile:
            json.dump(cellList, outfile, indent=4, separators=(',', ': '), sort_keys=False)
        return cellList
    else:
        return "ERROR"
#################
doesShutDown = False
def localhost():
    PORT = 9090
    os.chdir(getLeaflet(''))
#    os.chdir(os.path.abspath("..\\..\\leaflet"))
    Handler = MyHandler
    global doesShutDown

    doesShutDown = False
    socketserver.TCPServer.allow_reuse_address=True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:

        while doesShutDown == False:

            httpd.handle_request()


        doesShutDown = False



class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global doesShutDown
        if self.path ==  '/shutdown':
            doesShutDown = True
        else:
            doesShutDown = False

        http.server.SimpleHTTPRequestHandler.do_GET(self)
