import os
import pandas as pd
import json
from datetime import datetime
from constantPath import*
from math import sin, cos, sqrt, atan2, radians,floor
#import shapely
import shapely.geometry as geometry
from shapely.geometry import Point,Polygon
from PhoneId import*

import numpy as np
from shapely.ops import cascaded_union,polygonize
# from scipy.spatial import Delaunay

from TreeCreation import *
from shapely.geometry import MultiPoint,LinearRing
from scipy.spatial import Voronoi
from math import atan,sin,cos
# from area import area

class traceFromJson:
    def __init__(self,file,oper):
           self.ltephoneName = os.path.abspath(os.path.join(getPathText(""),file + "_" + "LTEphone"+"_"+oper.getOperater()+".txt"))
#        self.ltephoneName = os.path.abspath("/tmp/outputFiles/" + file + "_" + "LTEphone"+"_"+oper.getOperater()+".txt")
           self.jsonSystemInfoName = os.path.abspath(os.path.join(getPathText(""),file + "_" + "final"+"_"+oper.getOperater()+".txt"))
#        self.jsonSystemInfoName = os.path.abspath("/tmp/outputFiles/"+ file + "_" + "final"+ "_"+oper.getOperater()+".txt")
    # This function process  the LTE over-the-air(json file) which converted from pcap
    # return mcc, mnc and an object containing SIB informations
    def createTactable(self):
        df = pd.DataFrame({"TAC": [], "CellID": [], "PCI": [], "EARFCN": [], "geolocation": [],"mcc":[],"mnc":[]})
        jsonObject = open(self.jsonSystemInfoName)
        json_objects = json.load(jsonObject)
        jsonlist=[]
        mcc=""
        mnc=""
        for jsonfile in json_objects:
            dissector = jsonfile["_source"]["layers"]
            if "lte-rrc.BCCH_DL_SCH_Message_element" in (dissector).keys():
                typemess = dissector["lte-rrc.BCCH_DL_SCH_Message_element"]["lte-rrc.message_tree"]["lte-rrc.c1_tree"]
                sib1 = list((typemess).keys())[0]
                if sib1 == "lte-rrc.systemInformationBlockType1_element":
                    trackingAreaCode = typemess[sib1]["lte-rrc.cellAccessRelatedInfo_element"][
                        "lte-rrc.trackingAreaCode"]
                    mccdigit1=typemess[sib1]["lte-rrc.cellAccessRelatedInfo_element"][
                        "lte-rrc.plmn_IdentityList_tree"]["Item 0"]["lte-rrc.PLMN_IdentityInfo_element"][
                        "lte-rrc.plmn_Identity_element"]["lte-rrc.mcc_tree"]["Item 0"]["lte-rrc.MCC_MNC_Digit"]
                    mccdigit2 = typemess[sib1]["lte-rrc.cellAccessRelatedInfo_element"][
                        "lte-rrc.plmn_IdentityList_tree"]["Item 0"]["lte-rrc.PLMN_IdentityInfo_element"][
                        "lte-rrc.plmn_Identity_element"]["lte-rrc.mcc_tree"]["Item 1"]["lte-rrc.MCC_MNC_Digit"]
                    mccdigit3 = typemess[sib1]["lte-rrc.cellAccessRelatedInfo_element"][
                        "lte-rrc.plmn_IdentityList_tree"]["Item 0"]["lte-rrc.PLMN_IdentityInfo_element"][
                        "lte-rrc.plmn_Identity_element"]["lte-rrc.mcc_tree"]["Item 2"]["lte-rrc.MCC_MNC_Digit"]
                    mncdigit1=typemess[sib1]["lte-rrc.cellAccessRelatedInfo_element"][
                        "lte-rrc.plmn_IdentityList_tree"]["Item 0"]["lte-rrc.PLMN_IdentityInfo_element"][
                        "lte-rrc.plmn_Identity_element"]["lte-rrc.mnc_tree"]["Item 0"]["lte-rrc.MCC_MNC_Digit"]
                    mncdigit2 = typemess[sib1]["lte-rrc.cellAccessRelatedInfo_element"][
                        "lte-rrc.plmn_IdentityList_tree"]["Item 0"]["lte-rrc.PLMN_IdentityInfo_element"][
                                "lte-rrc.plmn_Identity_element"]["lte-rrc.mnc_tree"]["Item 1"]["lte-rrc.MCC_MNC_Digit"]

                    mcc=mccdigit1+mccdigit2+mccdigit3
                    mnc=mncdigit1+mncdigit2
                    cellId = typemess[sib1]["lte-rrc.cellAccessRelatedInfo_element"]["lte-rrc.cellIdentity"]
                    pci = dissector["frame"]["frame.comment"]["frame.comment.PCI"]
                    earfcn = dissector["frame"]["frame.comment"]["frame.comment.EARFCN"]

                    if (dissector["frame"]["frame.comment"]["frame.comment.geolocation"]["latitude"]!=""):
                        item={"SIB":{"TAC": trackingAreaCode, "CellID": cellId, "PCI": pci, "EARFCN": earfcn,
                                            "geolocation": {"lat":dissector["frame"]["frame.comment"]["frame.comment.geolocation"]["latitude"],
                                                            "lng":dissector["frame"]["frame.comment"]["frame.comment.geolocation"]["longitude"]},"mcc":mcc,"mnc":mnc}}
                        jsonlist.append(item)

        return  jsonlist,mcc,mnc

    # This function process  the LTE phone message
    # input: List of SIB object
    # return an object containing SIB object and mesurement object
    def createPCItable(self,frame_list):
        df = pd.DataFrame({"PCI": [], "EARFCN": [], "Geolocation": [],"RSRP":[],"neighbourMax_RSRP":[]})
        jsonLTE = open(self.ltephoneName)
        json_ltes = json.load(jsonLTE)
        for mersurement in json_ltes.keys():
            if (json_ltes[mersurement]["current cell"]["Geolocation"]["latitude"] != ""):
                pci = json_ltes[mersurement]["current cell"]["PCI"]
                rsrp= floor(140+float(json_ltes[mersurement]["current cell"]["RSRP"]["Average RSRP"]))+1
                geolocation = geometry.Point(float(json_ltes[mersurement]["current cell"]["Geolocation"]["latitude"]),float(json_ltes[mersurement]["current cell"]["Geolocation"]["longitude"]))
                earfcn = json_ltes[mersurement]["current cell"]["EARFCN"]
                # -------------------------

                neighbours = json_ltes[mersurement]["neighbours cells"]["neighbours.information"]
                rsrpneughbour=[]

                for index in neighbours.keys():
                    rsrpneughbour.append(int(neighbours[index]["RSRP"]))
                if len(rsrpneughbour)==0:
                    maxrsrp=-1000
                else:
                    maxrsrp = -max(rsrpneughbour) + int(json_ltes[mersurement]["current cell"]["RSRP"]["Average RSRP"])

                #------------------
                df3 = pd.DataFrame({"PCI": [pci], "EARFCN": [earfcn], "Geolocation": [geolocation],"RSRP":[rsrp], "neighbourMax_RSRP":[maxrsrp]})
                df = df.append(df3, ignore_index=True)
                pciEarfcnTable = df.groupby(["PCI", "EARFCN"],as_index=False)
                item={"Mesurement":{"PCI": pci, "EARFCN":earfcn, "Geolocation":{"lat":json_ltes[mersurement]["current cell"]["Geolocation"]["latitude"],
                                    "lng":json_ltes[mersurement]["current cell"]["Geolocation"]["longitude"]},"RSRP":rsrp, "neighbourMax_RSRP":maxrsrp}}
                frame_list.append(item)
        return  frame_list


###############################################################################################################

# This function process  create the site file for each operator
# input: operator name and operator object
# return site zone object and site frame.
def createSitefiles(operators, oper):
    group = operators.get_group((oper))
    group=group[group["Systeme"].str.startswith('LTE')]
    carte = pd.DataFrame(
        {"Numero du support": group["Numero du support"], "Numero Cartoradio": group["Numero Cartoradio"],
         "Azimut": group["Azimut"], "Exploitant": group["Exploitant"],
         "Systeme": group["Systeme"], "Longitude": group["Longitude"], "Latitude": group["Latitude"], "azimutMin": 0,
         "azimutMax": 0}).reset_index(drop=True)
    operatorName=str(oper)
    baseStationLocation=pd.DataFrame({"Numero Cartoradio":carte["Numero Cartoradio"],"Longitude":carte["Longitude"],
                                      "Latitude":carte["Latitude"],"bounded":"true"}).drop_duplicates().reset_index(drop=True)
    calAzimut = carte.reset_index(drop=True).groupby(["Numero Cartoradio","Systeme"])

    flag=False

    sites=[]

    for group in calAzimut.groups.keys():
        testnotorder=calAzimut.get_group((group))
        test=testnotorder.sort_values("Azimut").reset_index(drop=True)
        (supportnb,system)=group
        station = {"Identification_number":supportnb,"Latitude":test.iloc[0]["Latitude"],"Longitude":test.iloc[0]["Longitude"],"pointDestination":[],"pointZone":[]}
        listazimut=list(test["Azimut"])
        listazimut.append(listazimut[0])
        azimuttempo=0
        lngsite = test.iloc[0]["Longitude"]
        latsite = test.iloc[0]["Latitude"]
        intersectionZone=[]
        if (pd.isna(test["Azimut"]).iloc[0] == False):

            listazimut = list(test["Azimut"])
            listazimut.append(listazimut[0])
            azimuttempo = 0
            if test.shape[0]==1:
                var1 = listazimut[0]-60
                var2 = listazimut[0] +60
                carte.loc[(carte["Numero Cartoradio"] == supportnb) & (carte["Azimut"] == listazimut[0]) & (
                        carte["Systeme"] == system), ["azimutMax", "azimutMin"]] = [var1, var2]
                if (var1 > 0):
                    intersectionZone.append(var1)
                else:
                    intersectionZone.append(var1 + 360)
                if (var2 > 0):
                    intersectionZone.append(var2)
                else:
                    intersectionZone.append(var2 + 360)
            else:
                for i in range(0, test.shape[0]):
                    if listazimut[i] < listazimut[i + 1]:
                        var1 = (listazimut[i] + listazimut[i + 1]) * 0.5
                        if i == 0:
                            var2 = (listazimut[0] + listazimut[test.shape[0] - 1] - 360) * 0.5
                        else:
                            var2 = azimuttempo
                        carte.loc[(carte["Numero Cartoradio"] == supportnb) & (carte["Azimut"] == listazimut[i]) & (
                                carte["Systeme"] == system), ["azimutMax", "azimutMin"]] = [var1, var2]
                        azimuttempo = var1

                    else:
                        if (listazimut[i] + listazimut[i + 1] - 360) * 0.5 > 0:
                            var1 = (listazimut[i] + listazimut[i + 1] - 360) * 0.5
                        else:
                            var1 = (listazimut[i] + listazimut[i + 1] - 360) * 0.5 + 360

                        var2 = azimuttempo
                        carte.loc[(carte["Numero Cartoradio"] == supportnb) & (carte["Azimut"] == listazimut[i]) & (
                                carte["Systeme"] == system), ["azimutMax", "azimutMin"]] = [var1, var2]
                    if (var1 >= 0) and (var1 not in intersectionZone):
                        intersectionZone.append(var1)
                    if (var2 >= 0) and (var2 not in intersectionZone):
                        intersectionZone.append(var2)
            # calculate the distinaton on the direction of antenna
            for azimut in list(test["Azimut"]):
                station["pointDestination"].append(
                    {"lat": latsite + (0.5 * math.pow(10, -3)) * cos(azimut * np.pi / 180),
                     "lng": lngsite + (0.5 * math.pow(10, -3)) * sin(azimut * np.pi / 180)})
            # calculate the point for find the azimuth zone
            for element in intersectionZone: #sua o day 50 thanh 300
                station["pointZone"].append(
                    {"lat": latsite + (300 * math.pow(10, -3)) * cos(element * np.pi / 180),
                     "lng": lngsite + (300 * math.pow(10, -3)) * sin(element * np.pi / 180)})
            sites.append(station)
        else:
            carte.loc[(carte["Numero Cartoradio"] == supportnb) & (
                    carte["Systeme"] == system), ["azimutMax", "azimutMin"]] = [0, 360]
            sites.append(station)

    site_list_lat = baseStationLocation["Latitude"]
    site_list_lng = baseStationLocation["Longitude"]
    site_list = list(zip(site_list_lat, site_list_lng))
    (min_lat, min_lng, max_lat, max_lng) = Polygon(site_list).bounds
    id_count = 0
    sites_zone = {"id": id_count, "lat": min_lat, "lng": min_lng, "dlat": max_lat - min_lat, "dlng": 0, "zone": [],
                  "points": []}
    root= Node(min_lat,min_lng,max_lat - min_lat,max_lng-min_lng,sites)
    root.insert()
    site_zone=root.PreorderTraversal(root)
    return site_zone,carte

    print("done create the station table")

###############################################################################################################

# input: Tactable of LLE-over-the-air message , pciEarfcnTable of LTE-phone message and csv site file (the one is generated)
# return list of cell objects.
def cellInfo(Tactable,pciEarfcnTable,operatorDataframe):
    print("voronoi processing ")
    points = []
    regiontable = {}
    baseStationLocation = pd.DataFrame(
        {"Numero Cartoradio": operatorDataframe["Numero Cartoradio"], "Longitude": operatorDataframe["Longitude"],
         "Latitude": operatorDataframe["Latitude"], "bounded": "true"}).drop_duplicates()
    for index, row in (baseStationLocation).iterrows():
        points.append([row["Longitude"], row["Latitude"]])
    vor = Voronoi(list(points), qhull_options='Qbb Qc Qx')

    interpoint = vor.vertices  #  list of intersection points in the voronoi cell
    regionindices = vor.regions  # indices the region of voronoi cell
    for i, reg in enumerate(vor.regions):
        basesta = vor.points[np.where(vor.point_region == i)[0][0]]  # [long,lat]
        supportnum = (baseStationLocation).loc[
            (baseStationLocation['Longitude'] == basesta[0]) & (baseStationLocation['Latitude'] == basesta[1])][
            "Numero Cartoradio"]
        indexintable = supportnum.index.item()
        regiontable[str(supportnum.iloc[0])] = []
        if -1 in reg:
            baseStationLocation.loc[indexintable, "bounded"] = "false"
        for j in range(len(reg)):
            if reg[j] != -1:
                regiontable[str(supportnum.iloc[0])].append(vor.vertices[reg[j]])  # lng, lat
    print("voronoi processing done")
    #############################

    TACtable=Tactable.groupby(["TAC", "CellID"],as_index=False)
    df = pd.DataFrame()
    for tacTable in TACtable.groups.keys():

        for group, name in TACtable.get_group((tacTable)).groupby(["PCI", "EARFCN"]):
            pci,earfcn=group
            rowNum,colsNum=(TACtable.get_group((tacTable)).groupby(["PCI", "EARFCN"])).get_group((group)).shape
            pointc=geometry.Point(0,0)
            if rowNum>1:
                for i in range(1,rowNum):
                    pointA =(TACtable.get_group((tacTable)).groupby(["PCI", "EARFCN"])).get_group((group)).iloc[i-1]["geolocation"]
                    pointc=pointA
                    pointB = (TACtable.get_group((tacTable)).groupby(["PCI", "EARFCN"])).get_group((group)).iloc[i]["geolocation"]
                    if pointA.distance(pointB)>0:
                        df4 = pd.DataFrame(
                            {"cellID": [tacTable], "PCI": [pci], "EARFCN": [earfcn], "Geolocation": [pointA],"RSRP":[-1000],"RSRP_neighbor":[-1000]})
                        df = df.append(df4, sort=False ,ignore_index=True)

            if ((pci,earfcn)) in pciEarfcnTable.groups.keys():
                (rownum, colsnum) = (pciEarfcnTable.get_group((pci,earfcn))).shape
                for i in range(0,rownum):
                    pointD = pciEarfcnTable.get_group((pci, earfcn)).iloc[i]["Geolocation"]
                    rsrp= pciEarfcnTable.get_group((pci, earfcn)).iloc[i]["RSRP"]
                    rsrpNeighbor = pciEarfcnTable.get_group((pci, earfcn)).iloc[i]["neighbourMax_RSRP"]
                    if (distance(pointc,pointD) < 14):
                        df4 = pd.DataFrame({"cellID": [tacTable], "PCI": [pci], "EARFCN": [earfcn], "Geolocation": [pointD],"RSRP":[float(rsrp)],"RSRP_neighbor":[int(rsrpNeighbor)]})
                        df = df.append(df4,sort=False, ignore_index=True)

    Points=[]
    convex={}
    for group, name in df.groupby(["cellID", "PCI"]):
        gr=df.groupby(["cellID", "PCI"]).get_group(group)
        ((tac, cellid),pci) = group
        if gr.shape[0]> 250:
            if  list(gr.iloc[[0]]["EARFCN"])[0] not in convex.keys():
                convex[list(gr.iloc[[0]]["EARFCN"])[0]]=[]
                convex[list(gr.iloc[[0]]["EARFCN"])[0]].append(gr)
            else:
                convex[list(gr.iloc[[0]]["EARFCN"])[0]].append(gr)
    earfcn = list(convex.keys())  # point Lat, lng
    surfacetable = pd.DataFrame()

    for i in range(len(earfcn)):
        for j in range(len(convex[earfcn[i]])):
            pointinside = []
            pointborder = []
            pointvar = []
            Points = []
            points_table = {}
            (TAC, cellid) = convex[earfcn[i]][j].iloc[0]["cellID"]
            pci = convex[earfcn[i]][j].iloc[0]["PCI"]
            testpoints = []

            for index, rows in (convex[earfcn[i]][j]).iterrows():
                if rows["RSRP"] > 0:
                    if rows["Geolocation"] not in pointvar:
                        pointvar.append(rows["Geolocation"])
                    Points.append(
                        {"geo": rows["Geolocation"], "rsrp": rows["RSRP"], "rsrp_neighbour": rows["RSRP_neighbor"]})
            concave = geometry.MultiPoint(list(pointvar)).convex_hull
            x, y = concave.exterior.coords.xy
            for k in range(len(list(x))):
                testpoints.append(Point(x[k], y[k]))
            # ------------------
            for pointinP in Points:
                if pointinP["geo"].within(concave) == True:
                    pointinside.append(pointinP)
                else:
                    pointborder.append(pointinP)
            points_table["pointInside"] = pointinside
            points_table["concave"] = pointborder   # a supprimer
            points_table["pointBorder"] = testpoints
            surfacetable = surfacetable.append(
                pd.DataFrame({"cellID": [(TAC, cellid, pci)], "EARFCN": [earfcn[i]],
                              "polygon": [concave], "points": [points_table], "PointRSRP": [Points]}), sort=False,
                ignore_index=True)
    print("done create surface table")
    BaseStaCellrelation = pd.DataFrame()
    for indexCarte, row_Carte in operatorDataframe.iterrows():  # every antennes in cartoradio
        pointsgeo = [Point(p[1], p[0]) for p in regiontable[str(row_Carte["Numero Cartoradio"])]]
        regiongeo = MultiPoint(list(pointsgeo)).convex_hull

        azimutmin = row_Carte["azimutMin"]
        azimutmax = row_Carte["azimutMax"]

        bounded = baseStationLocation.loc[(baseStationLocation["Numero Cartoradio"] == row_Carte["Numero Cartoradio"])][
            "bounded"].iloc[0]
        for indexSurfTable, row_Surftable in surfacetable.iterrows():  # xet moi cell
            azicount = 0
            countcheck = 0
            surcount = 0
            if row_Carte["Systeme"] == getLTEBandname(row_Surftable["EARFCN"]):  # kiem tra co cung earfcn khong
                cellpolygon = row_Surftable["polygon"]
                if (regiongeo.intersects(cellpolygon) == True):  # kiem tra co giao nhau khong
                    pointrsrp = row_Surftable["PointRSRP"]
                    for pointR in pointrsrp:  # xet moi diem trong cell
                        weight = getWeight(pointR["rsrp"])
                        lat1 = (row_Carte["Latitude"]) * np.pi / 180
                        ln2 = (-row_Carte["Longitude"] + pointR["geo"].y) * np.pi / 180
                        lat2 = (pointR["geo"].x) * np.pi / 180
                        Y = cos(lat1) * ln2
                        X = lat2 - lat1
                        probleme = 0
                        azimuthXL = atan2(Y,X)*180/np.pi

                        if X == 0:
                            if Y > 0:
                                azimuth = 90
                            elif Y < 0:
                                azimuth = 270
                        else:
                            if (X > 0) and (Y > 0):
                                azimuth = atan(Y / X) * 180 / np.pi

                            elif (X > 0) and (Y < 0):
                                azimuth = atan(Y / X) * 180 / np.pi + 360

                            elif (X < 0) and (Y > 0):
                                azimuth = atan(Y / X) * 180 / np.pi + 180


                            else:
                                azimuth = atan(Y / X) * 180 / np.pi - 180 + 360

                        # check the point if it is in the right azimuth
                        if azimuth != azimuthXL:
                            probleme += 1

                        if azimutmin < 0:
                            if ((azimuth < azimutmax) or (azimuth > azimutmin + 360)):
                                azicount += weight
                                countcheck += 1
                                if bounded == "true":
                                    if regiongeo.contains(pointR["geo"]):
                                        surcount += weight
                        elif azimutmin > azimutmax:
                            if ((azimuth < azimutmax) or (azimuth > azimutmin)):
                                azicount += weight
                                countcheck += 1
                                if bounded == "true":
                                    if regiongeo.contains(pointR["geo"]):
                                        surcount += weight
                        else:
                            if ((azimuth < azimutmax) and (azimuth > azimutmin)):
                                azicount += weight
                                countcheck += 1
                                if bounded == "true":
                                    if regiongeo.contains(pointR["geo"]):
                                        surcount += weight
                    val = 0.8 * azicount / len(pointrsrp) + 0.2 * surcount / len(pointrsrp)
                    dfcal = pd.DataFrame(
                        {"NbIndentity": [row_Carte["Numero Cartoradio"]], "cellID": [row_Surftable["cellID"]],
                         "azimuth": [row_Carte["Azimut"]], "EARFCN": row_Surftable["EARFCN"],
                         "perAzimuth": [azicount / len(pointrsrp)], "perSurface": [surcount / len(pointrsrp)],
                         "val": [val]})
                    BaseStaCellrelation = BaseStaCellrelation.append(dfcal, sort=False, ignore_index=True)
    if BaseStaCellrelation.shape[0] >0:
        basedropped=BaseStaCellrelation[BaseStaCellrelation.perSurface >=0.25].reset_index(drop=True)
        print("done calculating the value of each cell")

        baseRelations=basedropped.groupby(["cellID"])
        dfresult = pd.DataFrame()
        for baserelation in baseRelations.groups.keys():
            gr=baseRelations.get_group((baserelation))
            varvalue = gr["val"].tolist()
            ind = np.argmax(varvalue)
            temp=ind
            flag_test=False
            for i in range(len(varvalue)):
                if (i!=ind):
                    if np.absolute(np.log10(varvalue[i]/varvalue[temp]))>0.08:
                        temp=ind
                        flag_test=True
                    else:
                        temp=-1
            if temp!=-1:
                dfresult = dfresult.append(pd.DataFrame({"cellID": [gr.iloc[temp]["cellID"]], "NbIndentity": [gr.iloc[temp]["NbIndentity"]],
                                                                   "azimuth": [gr.iloc[temp]["azimuth"]], "EARFCN": [gr.iloc[temp]["EARFCN"]],
                                                                   "perAzimuth": [gr.iloc[temp]["perAzimuth"]],
                                                                   "perSurface": [gr.iloc[temp]["perSurface"]],"val":[varvalue[temp]]}), sort=False, ignore_index=True)

        cellList = []
        temp_cellid = []
        if dfresult.shape[0]>0:
            Sitegroup=dfresult.groupby(["NbIndentity","azimuth","EARFCN"])
            dfResult=pd.DataFrame()
            for site in Sitegroup.groups.keys():
                gr=Sitegroup.get_group((site))
                if gr.shape[0] ==1:
                    dtf= pd.DataFrame({"cellID":[gr.iloc[0]["cellID"]],"NbIndentity":[gr.iloc[0]["NbIndentity"]],
                                                "azimuth":[gr.iloc[0]["azimuth"]], "EARFCN":[gr.iloc[0]["EARFCN"]],
                                                "perAzimuth": [gr.iloc[0]["perAzimuth"]],"perSurface": [gr.iloc[0]["perSurface"]],
                                                "val":[gr.iloc[0]["val"]]})#,sort=False, ignore_index=True
                    dfResult=dfResult.append(dtf)
                else:
                    (spnb, azi, earfcn) = site
                    latsite = baseStationLocation[baseStationLocation["Numero Cartoradio"] == spnb]["Latitude"]
                    lngsite = baseStationLocation[baseStationLocation["Numero Cartoradio"] == spnb]["Longitude"]
                    p = geometry.Point(latsite, lngsite)
                    distList=[]
                    for index, row_group in gr.iterrows():
                        temp_row = surfacetable.loc[(surfacetable["cellID"] == gr.iloc[temp]["cellID"])].index.values
                        pol_ext = LinearRing(surfacetable.iloc[temp_row[0]]["polygon"].exterior.coords)
                        d = pol_ext.project(p)
                        po = pol_ext.interpolate(d)
                        xx,yy=list(po.coords)[0]
                        closest_point_coords = Point(xx,yy)
                        distList.append(distance(p,closest_point_coords))
                    ind = np.argmin(varvalue)
                    dtf=pd.DataFrame({"cellID": [gr.iloc[ind]["cellID"]], "NbIndentity": [gr.iloc[ind]["NbIndentity"]],
                                                "azimuth": [gr.iloc[ind]["azimuth"]], "EARFCN": [gr.iloc[ind]["EARFCN"]],
                                                "perAzimuth": [gr.iloc[ind]["perAzimuth"]], "perSurface": [gr.iloc[ind]["perSurface"]],
                                                "val": [gr.iloc[ind]["val"]]})
                    dfResult=dfResult.append(dtf, sort=False,ignore_index=False)


            for j in range (dfResult.shape[0]):
                index_row=surfacetable[surfacetable["cellID"]== dfResult.iloc[j]["cellID"]].index.values
                siteaddlat=baseStationLocation[baseStationLocation["Numero Cartoradio"]==dfResult.iloc[j]["NbIndentity"]]["Latitude"].iloc[0]
                (TAC,cid,pci)=dfResult.iloc[j]["cellID"]
                cell = {"property": str((cid,pci,dfResult.iloc[j]["EARFCN"])),"TAC":TAC ,"features": [],
                        "site":float(dfResult.iloc[j]["NbIndentity"]),"Azimuth":str(dfResult.iloc[j]["azimuth"])}# {"lat":siteaddlat,"lng":siteaddlng}, }
                temp_cellid.append((TAC,cid))
                for point in surfacetable.iloc[index_row[0]]["points"]["pointInside"]:
                    cell["features"].append(
                        {"lat": point["geo"].x, "lon": point["geo"].y, "prop": "inside", "RSRP": point["rsrp"],"RSRP_neighbour": point["rsrp_neighbour"]})
                for point in surfacetable.iloc[index_row[0]]["points"]["concave"]:
                     cell["features"].append(
                         {"lat": point["geo"].x, "lon": point["geo"].y, "prop": "border", "RSRP": point["rsrp"],"RSRP_neighbour": point["rsrp_neighbour"]})

                for point in surfacetable.iloc[index_row[0]]["points"]["pointBorder"]:

                    cell["features"].append(
                        {"lat": point.x, "lon": point.y, "prop": "concave", "RSRP":-1000,"RSRP_neighbour": -1000})
                cellList.append(cell)

            print(dfResult.groupby(["NbIndentity","cellID","azimuth", "EARFCN","perAzimuth", "perSurface"]).size())

        ################################################ code for adding the cell without association to json object
        listAll = list(df["cellID"])
        disjoint = list(set(listAll).symmetric_difference(set(temp_cellid)))
        for cell_id in disjoint:
            tacval, cidval = cell_id
            tacgroup = df[df["cellID"] == cell_id].reset_index(drop=True)
            pcival = list(tacgroup["PCI"])[0]
            earfcnval = list(tacgroup["EARFCN"])[0]
            (rows, cols) = tacgroup.shape
            cell = {"property": str((cidval, pcival, earfcnval)), "TAC": tacval, "features": [],
                    "site": "None", "Azimuth": "None"}

            for index_tacgroup, row_tacgroup in tacgroup.iterrows():
                cell["features"].append(
                    {"lat": row_tacgroup["Geolocation"].x, "lon": row_tacgroup["Geolocation"].y, "prop": "border",
                     "RSRP": row_tacgroup["RSRP"],
                     "RSRP_neighbour": row_tacgroup["RSRP_neighbor"]})
            cellList.append(cell)
        print("done")
        return cellList

    else:
        return "ERROR"
