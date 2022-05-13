import os
from messages import *
from PhoneId import*
from traceMap import*
from os import path
import socketserver
import sys
import webbrowser
import http.server


def csvtoPcap(listfiles,directory):
    """This function converts field-test txt file from ZKsamp to pcap file and generate json file corresponding to
    field-test field.

    Parameters:
        listfiles: list of field-test file roots
        directory: path of working directory
    """
    files,filenames=readfile(listfiles)
    operator_dict={"oper":{},"mcc":{},"mnc":{}}
    for i in range(0,len(files)):
        
        #print("process file " + filenames[i])
        operaters = {}
        for line in files[i]: # browse each line of the zk file to find the terminal that is concerned
            words = line.split(",")
            line = words

            # Recognizing interesting lines in the zk file.
            if (line[0].find("@START") != 0):
                if (line[0].find("@END") != 0):
                    if (line[0]!="HB" and line[0]!="CO" and line[0]!="FE" ):    # look only for the interesting lines of the zk file
                        phoneid="phone_"+str(line[5])   # the terminal identity is in column 5
                        if (phoneid not in operaters.keys()):
                            operaters[phoneid] = operater(line[5])
                            operaters[phoneid].setMessages(line)
                        else:
                            operaters[phoneid].setMessages(line)
                        if (phoneid not in operator_dict.keys()):
                            operator_dict["oper"][phoneid] = []
        for oper in operaters.keys():
            try:
                print("Process the phone with phone id is " + operaters[oper].getOperater())
                MLmessages = mlMessageList()
                PLmessages = plMessages()

                # Getting operator information (such as location) obtained by parsing the ZK CSV file.
                groupname = operaters[oper].writejsonMessage(operaters[oper], MLmessages, PLmessages)
                pathjson = MLmessages.callWireshark(groupname, filenames[i], operaters[oper],operator_dict["oper"][operaters[oper].getOperater()])
                print("done call wireshark")

                # Merging geolocation data and ZK JSON.
                MLmessages.processingJson(pathjson, filenames[i], operaters[oper])
                print("done write json file of pcap")

                # Producing LTEPhone JSON file, which contains various information about the signal,
                # such as its power.
                PLmessages.writeLTEphoneJson(PLmessages.getMessages(), filenames[i], operaters[oper])
                print("done write ltephone json")

                # Creating PCI and TAC tables.

                trace = traceFromJson(filenames[i], operaters[oper])
                print("done get file json")
                jsonframes,mcc,mnc = trace.createTactable()
                operator_dict["mcc"][operaters[oper].getOperater()]=mcc
                operator_dict["mnc"][operaters[oper].getOperater()] = mnc
                print("done create tac table")
                jsonfile = trace.createPCItable(jsonframes)
                print("done create pci table")
                nameFile ="C"+mcc+"_"+mnc+"_"+filenames[i] + "_" + operaters[oper].getOperater() +".json"

                # Producing final JSON file.

                with open(os.path.join(directory,nameFile), 'w') as outfile:
                    json.dump(jsonfile, outfile, indent=4, separators=(',', ': '), sort_keys=False)
            except Exception as e:
                print("Error : {0} : {1}.".format(type(e).__name__, e))
    for operator in operator_dict["oper"].keys():
        try:
            if len(operator_dict["oper"][operator])!=0:
                callthark = [getWireshark("mergecap"), "-a", "-w",
                         os.path.join(directory, operator_dict["mcc"][operator]+"_"+operator_dict["mnc"][operator]+"_" + operator+".pcap")] + operator_dict["oper"][operator]
                subprocess.check_call(callthark)
        except Exception as e:
            print("Error : {0} : {1}.".format(type(e).__name__, e))
        





#XLXLXLXLXL : la conversion en json ne peut pas  etre supprimee car elle est utilise par le javascript mais elle conduit a avoir beaucoup trop de fichier
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
        {"Numero du support": res["Numéro de support"], "Numero Cartoradio": res["Numéro Cartoradio"],
         "Azimut": res["Azimut"], "Exploitant": res["Exploitant"],
         "Systeme": res["Système"],"Longitude":res["Longitude"],"Latitude": res["Latitude"],"azimutMin":0,"azimutMax":0}).drop_duplicates()

    # Grouping JSON data by antennas operators.
    operators=Antennas.groupby(["Exploitant"])
    operatorNames=["BOUYGUES TELECOM","FREE MOBILE","ORANGE","SFR"]

    # Creating dedicated files to each operator.
    for oper in operators.groups.keys():
        if oper in operatorNames:
            site_zone, carte=createSitefiles(operators, oper)

            # Producing site CSV file.
            carte.to_csv(directory+"/sites" + "_" + oper + ".csv", sep='\t', encoding='ISO-8859-1')

            # Producing JSON site zone file.
            with open(directory+"/sites" + "_" + oper + "_" + "Zone" + ".json", 'w') as outfile:
                json.dump(site_zone, outfile, indent=4, separators=(',', ': '), sort_keys=False)


#This function get  1 csv site file and  json field-test files for generating  json cells file
#in put is the listfiles and directory
#listfiles: list of site files root
#directory: path of working directory
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
