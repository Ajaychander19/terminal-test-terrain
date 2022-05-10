from datetime import datetime, timedelta, time,date
import subprocess
from constantPath import*
import json
import pandas as pd
import platform

#this class allows get the timestamp of messages
class messageType:
    def __init__(self,message):
        self.time=""
        self.message=message
        self.messageType=self.message[0]
    def getTime(self,j):
        timeArr = datetime.strptime(str(self.message[j]), '%H:%M:%S.%f')
        self.message[j] = (timeArr + timedelta(microseconds=1)).time()
        self.time=self.message[j]
        return self.time

#This class has the function for prcessing lte-over-the-air message
# function getCoordinates: get geolocation of trace
# function gettimeVar: get timestamp of trace
# function getPCIs: get PCI values
# function getEARFCNs: get EARFCN values
# function setMessages: store message into stack
# function processingJson: read the json file converted from pcap file and add the geolocation into this file
# function writejson: seperate the text file for each dissector
# function callWireshark: call the wireshark application for text2pcap. reodercap, and mergecap
# function writeText: write the right format of text for the input of text2pcap
# function writeTAList: write the tracking area
class mlMessageList:
    def __init__(self):
        self.PCIs=[]
        self.EARFCNs=[]
        self.coordinates=[]
        self.timeVar=[]
        self.stackmessage=[]

    def getCoordinates(self,message):
        coordinate = {"latitude": message[7], "longitude": message[8]}
        self.coordinates.append(coordinate)
        return self.coordinates

    def gettimeVar(self,message):
        self.timeVar.append(message[3])
        return self.timeVar

    def getPCIs(self,message):
        self.PCIs.append(message[20])
        return self.PCIs
    def getEARFCNs(self,message):
        self.EARFCNs.append(message[19])
        return self.EARFCNs
    def setMessages(self,message):
        self.stackmessage.append(message)
        return self.stackmessage

    def processingJson(self,pathnamefile, namefile,oper):
        json_objects = []

        with open(pathnamefile) as json_data:
            json_objects = json.load(json_data)

        for i in range(0, len(json_objects)):
            frame_object = json_objects[i]["_source"]["layers"]["frame"]
           # print(refindTrack(self.stackmessage[i]))
            frame_object["frame.comment"] = {"frame.comment.geolocation": self.coordinates[i], "frame.comment.PCI": self.PCIs[i],
                                             "frame.comment.EARFCN": self.EARFCNs[i],"frame.comment.tracking": refindTrack(self.stackmessage[i])}

        nameFile = namefile + "_" + "final"+ "_"+oper.getOperater()+".txt"
        with open(getPathText(nameFile), 'w') as outfile:
            json.dump(json_objects, outfile, indent=4, separators=(',', ': '), sort_keys=False)

    def writejson(self,stackmessage,timeVar,oper):
        BCCH_BCH_148 = []
        BCCH_DL_149 = []
        PCCH_DL_150 = []
        CCCH_DL_151 = []
        CCCH_UL_152 = []
        DCCH_DL_153 = []
        DCCH_UL_154 = []
        Dis_group = [BCCH_BCH_148, BCCH_DL_149, PCCH_DL_150, CCCH_DL_151, CCCH_UL_152, DCCH_DL_153, DCCH_UL_154]
        Dis_groupName = ["BCCH_BCH_148"+ "_"+oper.getOperater(), "BCCH_DL_149"+ "_"+oper.getOperater(), "PCCH_DL_150"+ "_"+oper.getOperater(),
                         "CCCH_DL_151"+ "_"+oper.getOperater(), "CCCH_UL_152"+ "_"+oper.getOperater(), "DCCH_DL_153"+ "_"+oper.getOperater(),"DCCH_UL_154"+ "_"+oper.getOperater()]
        for i in range(0, len(stackmessage)):
            if (i > 0):
                time_object = datetime.strptime(str(stackmessage[i - 1][3]), '%H:%M:%S.%f')
                if (timeVar[i] == timeVar[i - 1]):
                    stackmessage[i][3] = (time_object + timedelta(microseconds=1)).time()
            self.getCoordinates(stackmessage[i])
            if (stackmessage[i][33] == "BC" and stackmessage[i][34] == "BCH"):
                BCCH_BCH_148.append(stackmessage[i])
            elif (stackmessage[i][33] == "BC" and stackmessage[i][34] == "DL-S"):
                BCCH_DL_149.append(stackmessage[i])
            elif (stackmessage[i][33] == "PC" and stackmessage[i][34] == "DL-S"):
                PCCH_DL_150.append(stackmessage[i])
            elif (stackmessage[i][33] == "CC" and stackmessage[i][34] == "DL-S"):
                CCCH_DL_151.append(stackmessage[i])
            elif (stackmessage[i][33] == "CC" and stackmessage[i][34] == "UL-S"):
                CCCH_UL_152.append(stackmessage[i])
            elif (stackmessage[i][33] == "DC" and stackmessage[i][34] == "DL-S"):
                DCCH_DL_153.append(stackmessage[i])
            elif (stackmessage[i][33] == "DC" and stackmessage[i][34] == "UL-S"):
                DCCH_UL_154.append(stackmessage[i])
        for j in range(0, len(Dis_group)):
            self.writeText(Dis_group[j],Dis_groupName[j], 40)
        return Dis_groupName

    def callWireshark(self,nameFiles, filename,oper,wiresharkNames):
        DLT_key = {"BCCH_BCH_148"+ "_"+oper.getOperater(): "148",
                   "BCCH_DL_149"+ "_"+oper.getOperater(): "149",
                   "PCCH_DL_150"+ "_"+oper.getOperater(): "150",
                   "CCCH_DL_151"+ "_"+oper.getOperater(): "151",
                   "CCCH_UL_152"+ "_"+oper.getOperater(): "152",
                   "DCCH_DL_153"+ "_"+oper.getOperater(): "153",
                   "DCCH_UL_154"+ "_"+oper.getOperater(): "154"}
        root = getPathText("") + ("\\" if platform.system()=="Windows" else "")   # Specifique Windows retire
        disGroup = []
        for nameFile in nameFiles:
            name = "%s.txt" % str(nameFile)
            pathInfile = os.path.abspath(os.path.join(root,name))
            pathOutfile = os.path.abspath(os.path.join(root,"%s.pcap" % str(nameFile)))
            #pathOutfile = root + "%s.pcap" % str(nameFile)
            disGroup.append(pathOutfile)
            subprocess.check_call(
                [getWireshark("text2pcap"), "-l", DLT_key[nameFile], "-t", "%Y-%m-%d %H:%M:%S.", pathInfile,
                 pathOutfile])

        path =  os.path.abspath(os.path.join(root,filename + "_" +"_"+oper.getOperater()+ "final.pcap"))
        pathorder=os.path.abspath(os.path.join(root, filename + "_" + "_" + oper.getOperater() + "final_order.pcap"))
        pathjson=os.path.abspath(os.path.join(root, filename + "_" + "_" + oper.getOperater() + "json.txt"))

        #pathorder=root + filename + "_" +"_"+oper.getOperater()+ "final_order.pcap"
        #pathjson = root + filename + "_"+oper.getOperater()+"_" + "json.txt"

        subprocess.check_call(
            [getWireshark("mergecap"),"-a" ,"-w", path, disGroup[0], disGroup[1], disGroup[2]
                , disGroup[3], disGroup[4], disGroup[5], disGroup[6]])

        reordercheck=subprocess.check_output(
            [getWireshark("reordercap"), "-n", path,pathorder])
        if (reordercheck.decode("utf-8").split(" ")[2]!="0"):
            tsharkCall = [getWireshark("tshark"), "-T", "json", "-r", pathorder]
        else:
            print("ordered file")
            tsharkCall = [getWireshark("tshark"), "-T", "json", "-r",
                          path]  # export ra file json theo file pcap sau khi sap xep
        with open(pathjson, "wb") as tsharkOpen:
            subprocess.call(tsharkCall, stdout=tsharkOpen)

        wiresharkNames.append(path)
        return pathjson

    def writeText(self,message_list, name, start_position):
        path = getPathText(str(name)+".txt")
        with open(path, 'w') as f:
            for mess in message_list:
                time = mess[2] + " " + str(mess[3])
                f.write(time)
                f.write("\n")
                f.write("0000")
                for j in range(start_position, len(mess)):
                    f.write(" ")
                    f.write(str(mess[j]))
                f.write("\n")

    def writeTAList(self,TACtable,oper):
        tac=TACtable.drop(["geolocation"], axis=1)
        Tactable=tac.drop_duplicates()
        tacstable=Tactable.groupby(["TAC"],as_index=False)
        ta={"mcc":Tactable.iloc[0]["mcc"],"mnc":Tactable.iloc[0]["mnc"],"TAList":[]}
        for tac in tacstable.groups.keys():
            gr=tacstable.get_group(tac)
            tracking={"TAC":tac,"cell":[]}
            for index, row in gr.iterrows():
                tracking["cell"].append({"cellId":row["CellID"],"PCI":row["PCI"],"EARFCN":row["EARFCN"]})
            ta["TAList"].append(tracking)
        name= "TrackingAreaList" + "_"+oper.getOperater()+".txt"
        with open(getPathText(name), 'w') as outfile:
            json.dump(ta, outfile, indent=4, separators=(',', ': '), sort_keys=False)


#this class has the function for procesing the lte phone message
# function setMessages : store the message into stack
# function getMessages : get the stack
# function writeLTEphoneJson : write the lte phone message in the json format.
class plMessages():
    def __init__(self):
        self.messages=[]
    def setMessages(self,message):
        self.messages.append(message)
    def getMessages(self):
        return self.messages

    def writeLTEphoneJson(self,file, namefile,oper):
        df = pd.DataFrame(file)
        df1 = df[df.columns[71:]]
        df.drop(df.columns[71:], axis=1, inplace=True)
        df.drop(df.columns[52:70], axis=1, inplace=True)
        df.drop(df.columns[47:50], axis=1, inplace=True)
        df.drop(df.columns[
                    [0, 1, 4, 5, 6, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25, 28, 29, 30, 31, 32, 33,
                     37, 38, 42, 43]], axis=1, inplace=True)
        df.columns = ["Date", "Time", "Latitude", "Longitude", "Altitude", "Mode", "EARFCN", "PCI", "Average RSRP",
                      "RSRP Antenna 0", "RSRP Antenna 1", "Average RSRQ", "RSRQ Antenna 0", "RSRQ Antenna 1",
                      "Average RSSI"
            , "RSSI Antenna 0", "RSSI Antenna 1", "SINR Antenna 0", "SINR Antenna 1", "Number of neighbours"]
        json_objects = dict()
        for index, row in df.iterrows():
            json_obj = dict()
            neighbourList = dict()
            if row["Mode"] == "I":
                row["Mode"] = "idle"
            elif row["Mode"] == "C":
                row["Mode"] = "connected"
            # Find the infos of the neighbours cells
            neighbourCount = 0
            neighbourList = {}
            for i in range(0, len(df1.columns), 20):
                if df1.iloc[index][71 + i + 4] is not None:
                    neighbourCount += 1
                    neighbourList["neighbour " + str(neighbourCount)] = {"PCI": df1.iloc[index][71 + i + 4],
                                                                         "RSRP": df1.iloc[index][71 + i + 6],
                                                                         "RSRQ": df1.iloc[index][71 + i + 7],
                                                                         "RSSI": df1.iloc[index][71 + i + 8]}

            # Prepare the json file
            json_obj["current cell"] = {}
            # json_obj["current cell"]["Date"]=row["Date"]
            time = str(row["Time"].strftime('%H:%M:%S.%f'))
            json_obj["current cell"]["Time"] = str(row["Date"]) + " " + time

            json_obj["current cell"]["Geolocation"] = {"latitude": row["Latitude"], "longitude": row["Longitude"]}

            json_obj["current cell"]["Mode"] = row["Mode"]
            json_obj["current cell"]["PCI"] = row["PCI"]
            json_obj["current cell"]["EARFCN"] = row["EARFCN"]
            json_obj["current cell"]["RSRP"] = {"Average RSRP": row["Average RSRP"],
                                                "RSRP Antenna 0": row["RSRP Antenna 0"],
                                                "RSRP Antenna 1": row["RSRP Antenna 1"]}
            json_obj["current cell"]["RSRQ"] = {"Average RSRQ": row["Average RSRQ"],
                                                "RSRQ Antenna 0": row["RSRQ Antenna 0"],
                                                "RSRQ Antenna 1": row["RSRQ Antenna 1"]}
            json_obj["current cell"]["RSSI"] = {"Average RSSI": row["Average RSSI"],
                                                "RSSI Antenna 0": row["RSSI Antenna 0"],
                                                "RSSI Antenna 1": row["RSSI Antenna 1"]}
            json_obj["current cell"]["SINR"] = {"SINR Antenna 0": row["SINR Antenna 0"],
                                                "SINR Antenna 1": row["SINR Antenna 1"]}
            json_obj["neighbours cells"] = {}
            json_obj["neighbours cells"]["Number of neighbours"] = row["Number of neighbours"]
            json_obj["neighbours cells"]["neighbours.information"] = neighbourList

            json_objects["Measurement " + str(index)] = json_obj

        nameFile = namefile + "_" + "LTEphone"+"_"+oper.getOperater()+".txt"

        with open(getPathText(nameFile), 'w') as outfile:
            json.dump(json_objects, outfile, indent=4, separators=(',', ': '), sort_keys=False)
#######################################
