import os
import platform
import ntpath
import math
from os import path
from math import sin, cos, sqrt, atan2, radians
from datetime import time

# this function gets the path of the temporary directoy (outputFiles)
def getPathText(name):
#     print('code origine :', os.path.abspath("..\\outputFiles\\" + name))
    if os.path.isdir(os.path.abspath(name)):
        #        print('youp la boum1:', os.path.normpath(os.path.join(os.path.abspath(name), os.path.pardir, 'outputFiles', name)))
        return os.path.normpath(os.path.join(os.path.abspath(name), os.path.pardir, 'outputFiles', name))
    else:
        #print('youp la boum2:', os.path.normpath(os.path.join(os.path.abspath(name), os.path.pardir, os.path.pardir, 'outputFiles', name)))
        return os.path.normpath(os.path.join(os.path.abspath(name), os.path.pardir, os.path.pardir,  'outputFiles', name))
    #return os.path.abspath("..\\outputFiles\\" + name)

# this function gets the path of the html directory
def getLeaflet(name):
    return os.path.abspath(os.path.join(os.path.abspath(name),os.path.pardir,os.path.pardir,'leaflet',name))
#    return os.path.abspath("..\\..\\leaflet\\" + name)

# this function gets the path of wireshark application
# input: name of the application
def getWireshark(application):
    if platform.system()=="Windows":
        return "C:\\Program Files\\Wireshark\\"+application
    else:
        return application


def  getSelfDir(truc):
    return os.path.abspath(truc)


# this function returns the name of earfcn values
def getLTEBandname(earfcn):
    valearfcn=int(earfcn)
    band="unknown"
    if valearfcn<600:
        band="LTE 2100"
    elif valearfcn<1200:
        band = "LTE 1900"
    elif valearfcn < 1200:
        band = "LTE 1900"
    elif valearfcn < 1950:
        band = "LTE 1800"
    elif valearfcn < 2400:
        band = "LTE 2100"
    elif valearfcn < 2650:
        band = "LTE 800"
    elif valearfcn < 2750:
        band = "LTE 800"
    elif valearfcn < 3800:
        band = "LTE 800"
    elif valearfcn < 4150:
        band = "LTE 1800"
    elif valearfcn < 4750:
        band = "LTE 2100"
    elif valearfcn < 5010:
        band = "LTE 1500"
    elif valearfcn < 5180:
        band = "LTE 700"
    elif valearfcn < 5280:
        band = "LTE 700"
    elif valearfcn < 5380:
        band = "LTE 700"
    elif valearfcn < 5730:
        band = "unknown"
    elif valearfcn < 5850:
        band = "LTE 700"
    elif valearfcn < 6000:
        band = "LTE 800"
    elif valearfcn < 6150:
        band = "LTE 800"
    elif valearfcn < 6450:
        band = "LTE 800"   # a verifier
    elif valearfcn < 6600:
        band = "LTE 1500"
    elif valearfcn < 7500:
        band = "LTE 3500"
    elif valearfcn < 7700:
        band = "LTE 2100"
    elif valearfcn < 8040:
        band = "LTE 1500"
    elif valearfcn < 8690:
        band = "LTE 1900"
    elif valearfcn < 9040:
        band = "LTE 800"
    elif valearfcn < 9210:
        band = "LTE 800"
    elif valearfcn < 9660:
        band = "LTE 700"
    elif valearfcn < 9870:
        band = "LTE 700"
    elif valearfcn < 9920:
        band = "LTE 400"
    elif valearfcn < 36000:
        band = "unknown"
#    print("find the frequency of " + earfcn + " which is "+ band)
#   band={"3000":"LTE 2600","1300":"LTE 1800","6400":"LTE 800","0":"LTE 2100","1501":"LTE 1800","2825":"LTE 2600","6300":"LTE 800","6200":"LTE 800"}
    return band

# this function get the name of in the path
def getfileName(path):
    return ntpath.split(os.path.splitext(path)[0])[1]

# this function read a list of file roots and return the contain and the name
def readfile(pathfile):
    files=[]
    filenames=[]
    for file in pathfile:
        filename = getfileName(file)
        file = open(file, "r")
        files.append(file)
        filenames.append(filename)
    return files,filenames

#This function calculate the distance in km of 2 points
def distance(pointA,pointB):
    R=6373.0
    lat1 = radians(pointA.x)
    lon1 = radians(pointA.y)
    lat2 = radians(pointB.x)
    lon2 = radians(pointA.y)
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c #unit in km

#This function get the weight based on the rsrp value
def getWeight(rsrp):
    if int(rsrp) <=41:
        return 0.15
    elif int(rsrp) >= 61:
        return  1
    else:
        return 0.6

#This function return the trace
def refindTrack(list):
    track=""
    for element in list:
        if isinstance(element,time):
            track+=","+element.strftime('%H:%M:%S.%f')
        else:
            track += "," + element
    return track
#######################
