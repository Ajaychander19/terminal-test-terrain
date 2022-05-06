import os
from messages import *
from PhoneId import*
from traceMap import*
from os import path

#This function convert field-test file txt from ZKsamp to pcap file and generate json file correspond to field-test field
#in put is the listfiles and directory
#listfiles: list of field-test file roots
#directory: path of working directory
def csvtoPcap(listfiles,directory):
    files,filenames=readfile(listfiles)
    operator_dict={"oper":{},"mcc":{},"mnc":{}}
    for i in range(0,len(files)):
        print("process file " + filenames[i])
        operaters = {}
        for line in files[i]:
            words = line.split(",")
            line = words
            if (line[0].find("@START") != 0):
                if (line[0].find("@END") != 0):
                    if (line[0]!="HB" and line[0]!="CO" and line[0]!="FE" ):
                        phoneid="phone_"+str(line[5])
                        if (phoneid not in operaters.keys()):
                            operaters[phoneid] = operater(line[5])
                            operaters[phoneid].setMessages(line)
                        else:
                            operaters[phoneid].setMessages(line)
                        if (phoneid not in operator_dict.keys()):
                            operator_dict["oper"][phoneid] = []
        for oper in operaters.keys():
            print("Process the phone with phone id is " + operaters[oper].getOperater())
            MLmessages = mlMessageList()
            PLmessages = plMessages()
            groupname = operaters[oper].writejsonMessage(operaters[oper], MLmessages, PLmessages)
            pathjson = MLmessages.callWireshark(groupname, filenames[i], operaters[oper],operator_dict["oper"][operaters[oper].getOperater()])
            print("done call wireshark")
            MLmessages.processingJson(pathjson, filenames[i], operaters[oper])
            print("done write file json of pcap")
            PLmessages.writeLTEphoneJson(PLmessages.getMessages(), filenames[i], operaters[oper])
            print("done write ltephone json")
            trace = traceFromJson(filenames[i], operaters[oper])
            print("done get file json")
            jsonframes,mcc,mnc = trace.createTactable()
            operator_dict["mcc"][operaters[oper].getOperater()]=mcc
            operator_dict["mnc"][operaters[oper].getOperater()] = mnc
            print("done create tac table")
            jsonfile = trace.createPCItable(jsonframes)
            print("done create pci table")
            nameFile ="C"+mcc+"_"+mnc+"_"+filenames[i] + "_" + operaters[oper].getOperater() +".json"
            with open(os.path.join(directory,nameFile), 'w') as outfile:
                json.dump(jsonfile, outfile, indent=4, separators=(',', ': '), sort_keys=False)
    for operator in operator_dict["oper"].keys():

        if len(operator_dict["oper"][operator])!=0:
            callthark = [getWireshark("mergecap"), "-a", "-w",
                         os.path.join(directory, operator_dict["mcc"][operator]+"_"+operator_dict["mnc"][operator]+"_" + operator+".pcap")] + operator_dict["oper"][operator]
            subprocess.check_call(callthark)





#This function get 2 files of cartoratdio and generate 1 csv file with information using (and 1 json file for visualisation)
#in put is the listfiles and directory
#listfiles: list of site files root
#directory: path of working directory
#XLXLXLXLXL : la conversion en json ne peut pas  etre supprimee car elle est utilise par le javascript mais elle conduit a avoir beaucoup trop de fichier
def createSite_json(listfiles,directory):
    df0 = pd.read_csv(listfiles[0],sep=';',encoding='ISO-8859-1')
    df1 = pd.read_csv(listfiles[1],sep=';',encoding='ISO-8859-1')
    if (df0.shape[0]>df1.shape[0]):
        df1.set_index("Numéro du support", inplace=True)
        res=df0.join(df1, on='Numéro de support',how='left')
    else:
        df0.set_index("Numéro du support", inplace=True)
        res = df1.join(df0, on='Numéro de support', how='left')
    Antennas = pd.DataFrame(
        {"Numero du support": res["Numéro de support"], "Numero Cartoradio": res["Numéro Cartoradio"],
         "Azimut": res["Azimut"], "Exploitant": res["Exploitant"],
         "Systeme": res["Système"],"Longitude":res["Longitude"],"Latitude": res["Latitude"],"azimutMin":0,"azimutMax":0}).drop_duplicates()
    operators=Antennas.groupby(["Exploitant"])
    operatorNames=["BOUYGUES TELECOM","FREE MOBILE","ORANGE","SFR"]
    for oper in operators.groups.keys():
        if oper in operatorNames:
            site_zone, carte=createSitefiles(operators, oper)
            carte.to_csv(directory+"/sites" + "_" + oper + ".csv", sep='\t', encoding='ISO-8859-1')
            with open(directory+"/sites" + "_" + oper + "_" + "Zone" + ".json", 'w') as outfile:
                json.dump(site_zone, outfile, indent=4, separators=(',', ': '), sort_keys=False)




#This function get  1 csv site file and  json field-test files for generating  json cells file
#in put is the listfiles and directory
#listfiles: list of site files root
#directory: path of working directory
def Associate_cell(listfiles,directory):
    lteTable=pd.DataFrame()
    TACtable=pd.DataFrame()
    carte = pd.DataFrame()
    filename=""
    for file in listfiles:
        if (getfileName(file).split("_")[0]=="sites"):
            filename=getfileName(file.split("_")[1])
            df=pd.read_csv(file,sep='\t', encoding="ISO-8859-1")
            carte = pd.DataFrame(
                {"Numero Cartoradio": df["Numero Cartoradio"], "Azimut": df["Azimut"], "Systeme": df["Systeme"],
                 "Longitude": df["Longitude"], "Latitude": df["Latitude"], "azimutMin": df["azimutMin"], "azimutMax": df["azimutMax"]})
        else:
            json_data = open(file)
            json_objects = json.load(json_data)
            for item in json_objects:
                if (list(item.keys())[0]== "SIB"):
                    coord = geometry.Point(
                        float(item["SIB"]["geolocation"]["lat"]),
                        float(item["SIB"]["geolocation"]["lng"]))
                    df=pd.DataFrame({"TAC": [item["SIB"]["TAC"]], "CellID": [item["SIB"]["CellID"]],
                                     "PCI": [item["SIB"]["PCI"]], "EARFCN": [item["SIB"]["EARFCN"]],
                                     "geolocation": [coord],"mcc":[item["SIB"]["mcc"]],"mnc":[item["SIB"]["mnc"]]})
                    TACtable=TACtable.append(df,sort=False,ignore_index=True)

                if (list(item.keys())[0]== "Mesurement"):
                    coord = geometry.Point(
                        float(item["Mesurement"]["Geolocation"]["lat"]),
                        float(item["Mesurement"]["Geolocation"]["lng"]))
                    df=pd.DataFrame({"PCI": [item["Mesurement"]["PCI"]], "EARFCN": [item["Mesurement"]["EARFCN"]],
                                     "Geolocation": [coord],"RSRP":[item["Mesurement"]["RSRP"]],"neighbourMax_RSRP":[item["Mesurement"]["neighbourMax_RSRP"]]})
                    lteTable=lteTable.append(df,sort=False,ignore_index=True)
    print("reading done")
    pciEarfcnTable =lteTable.groupby(["PCI", "EARFCN"], as_index=False)
    cellList=cellInfo(TACtable, pciEarfcnTable, carte)
    if cellList!="ERROR":
        with open(os.path.join(directory,filename + "_association.json"), 'w') as outfile:
            json.dump(cellList, outfile, indent=4, separators=(',', ': '), sort_keys=False)
        return cellList
    else:
        return "ERROR"
#################
import socketserver
import sys
import webbrowser
import http.server
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
