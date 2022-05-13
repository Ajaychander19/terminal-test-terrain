from datetime import datetime, timedelta, time
import subprocess
from constantPath import*
import json
import pandas as pd
from messages import*


class operater:
    """This class has the function every operator (?)
    This class defines functions for each operator.
    """
    def __init__(self,phoneid):
        self.phoneid="phone_"+str(phoneid)
        self.typeMessages=[]
        self.messages=[]
        self.mcc=""
        self.mnc=""

    def getMcc(self):
        """Gets the MCC value"""
        return self.mcc

    def getMnc(self):
        """Gets the mnc value"""
        return self.mnc

    def getOperater(self):
        """Gets the name of the operator"""
        return self.phoneid

    def setMcc(self, mcc):
        """Changes self.mcc attribute with mcc parameter"""
        self.mcc = mcc

    def setMnc(self, mnc):
        """Changes self.mcc attribute with mnc parameter"""
        self.mnc = mnc

    def setTypemess(self,mess):
        """Stores the type message.

        Parameters:
            mess: message.
        """
        self.typeMessages.append(mess[0])

    def setMessages(self, message):
        """Stores messages from the same operator into a stack

        Parameters:
            message: message to store.
        """
        self.messages.append(message)

    def getMessages(self):
        """Gets the messages stack."""
        return self.messages

    def writejsonMessage(self, oper, MLmessages, PLmessages):
        """Copy operators messages data into the corresponding message
        processing objects (mlMessages or plMessages).
        Produces temporary text2pcap input files using mlMessages.writejson.

        Parameters :
            oper: operator data message.
            MLmessages: LTE over-the-air mlMessages processing object.
            PLMessages: LTEPhone plMessages processing object.
        """
        for line in oper.messages:
            messagetype=messageType(line)
            messagetype.getTime(3)

            # LTE OTA Message
            if (messagetype.messageType == "ML"):
                MLmessages.gettimeVar(messagetype.message)
                MLmessages.getPCIs(messagetype.message)
                MLmessages.getEARFCNs(messagetype.message)
                MLmessages.setMessages(messagetype.message)
            elif (messagetype.messageType == "PL"): # LTEPhone message
                PLmessages.setMessages(messagetype.message)

        groupname=MLmessages.writejson(MLmessages.stackmessage,MLmessages.timeVar,oper)
        return groupname



