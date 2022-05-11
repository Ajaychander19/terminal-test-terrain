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
        """get the mcc value"""
        return self.mcc
    def getMnc(self):
        """get the mnc value"""
        return self.mnc

    def getOperater(self):
        """get the name of the operator"""
        return self.phoneid

    def setMcc(self,mcc):
        """changes self.mcc attribute with mcc parameter"""
        self.mcc=mcc

    def setMnc(self,mnc):
        """changes self.mcc attribute with mnc parameter"""
        self.mnc=mnc

    def setTypemess(self,mess):
        """store the type message"""
        self.typeMessages.append(mess[0])

    def setMessages(self,message):
        """store message (?) from (?) the same operator into a stack"""
        self.messages.append(message)

    def getMessages(self):
        """get the messages stack."""
        return self.messages

    def writejsonMessage(self,oper,MLmessages,PLmessages):
        """get the information from messages into the operator attribute
        return the group of messages in the same dissector
        """
        for line in oper.messages:
            messagetype=messageType(line)
            messagetype.getTime(3)
            if (messagetype.messageType == "ML"):
                MLmessages.gettimeVar(messagetype.message)
                MLmessages.getPCIs(messagetype.message)
                MLmessages.getEARFCNs(messagetype.message)
                MLmessages.setMessages(messagetype.message)
            elif (messagetype.messageType == "PL"):
                PLmessages.setMessages(messagetype.message)
        groupname=MLmessages.writejson(MLmessages.stackmessage,MLmessages.timeVar,oper)
        return groupname



