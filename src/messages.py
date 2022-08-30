from datetime import datetime, timedelta, time,date
import subprocess
from constantPath import*
import json
import pandas as pd
import platform


class messageType:
    """This class represents a message, defined by its content and its timestamp."""

    def __init__(self, message):
        """Class constructor

        Parameters:
            message: message content.
        """
        self.time=""
        self.message=message
        self.messageType=self.message[0]

    def getTime(self, j):
        """Adds one microsecond to the message timestamp,
        and returns it. This is done in order to allow
        mergecap or / and reordercap to properly order the messages
        by increasing timestamp, as the unmodified messages can be produced at the
        same second, and therefore cannot be distinguished by their timestamp.

        Parameters:
            j: timestamp index in the message.
        """
        timeArr = datetime.strptime(str(self.message[j]), '%H:%M:%S.%f')
        self.message[j] = (timeArr + timedelta(microseconds=1)).time()
        self.time=self.message[j]
        return self.time

class mlMessageList:
    """This class defines functions for processing lte-over-the-air messages"""

    def __init__(self):
        self.PCIs=[]
        self.EARFCNs=[]
        self.coordinates=[]
        self.timeVar=[]
        self.stackmessage=[]

    def getCoordinates(self,message):
        """Gets the geolocation of the trace
        Parameters:
            message: LTE OTA message.
        """
        coordinate = {"latitude": message[7], "longitude": message[8]}
        self.coordinates.append(coordinate)
        return self.coordinates

    def gettimeVar(self,message):
        """Gets the timestamp of the trace
        Parameters:
            message: LTE OTA message.
        """
        self.timeVar.append(message[3])
        return self.timeVar

    def getPCIs(self,message):
        """Gets PCI values
        Parameters:
            message: LTE OTA message.
        """
        self.PCIs.append(message[20])
        return self.PCIs

    def getEARFCNs(self,message):
        """Gets EARFCN values
        Parameters:
            message: LTE OTA message.
        """
        self.EARFCNs.append(message[19])
        return self.EARFCNs

    def setMessages(self,message):
        """Stores message into the stack
            message: LTE OTA message.
        """
        self.stackmessage.append(message)
        return self.stackmessage


class plMessages():
    """This class defines functions to process LTEPhone messages"""

    def __init__(self):
        self.messages=[]

    def setMessages(self,message):
        """Stores a message into the message stack.

        Parameter:
            message: message to store.
        """
        self.messages.append(message)

    def getMessages(self):
        """Gets the message stack"""
        return self.messages
