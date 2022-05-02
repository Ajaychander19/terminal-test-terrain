from datetime import datetime, timedelta, time
import subprocess
from constantPath import*
import json
import pandas as pd
from messages import*


#This class has the function every operator
# fucntion getMCC: get the mcc value
# function getMnc: get the mnc value
# function setMCC: set the MCC to the attribute
# function setMnc: set the Mnc to the attribute
# function getOperater: get the name id of operator
# function setTypemess: store the type message
# fucnton setMessages : store message the same operator into a stack
# fucnton getMessages : get the stack message.
# fucnton writejsonMessage : get the informations of message into attribute of operator
# return the group of messages in the same dissector
class operater:
    def __init__(self,phoneid):
        self.phoneid="phone_"+str(phoneid)
        self.typeMessages=[]
        self.messages=[]
        self.mcc=""
        self.mnc=""
    def getMcc(self):
        return self.mcc
    def getMnc(self):
        return self.mnc
    def getOperater(self):
        return self.phoneid
    def setMcc(self,mcc):
        self.mcc=mcc
    def setMnc(self,mnc):
        self.mnc=mnc
    def setTypemess(self,mess):
        self.typeMessages.append(mess[0])

    def setMessages(self,message):
        self.messages.append(message)

    def getMessages(self):
        return self.messages

    def writejsonMessage(self,oper,MLmessages,PLmessages):
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



