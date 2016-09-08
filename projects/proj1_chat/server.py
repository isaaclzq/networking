import socket
import select
import sys
from utils import *

def pad_message(message):
    while len(message) < MESSAGE_LENGTH:
        message += " "
    return message[:MESSAGE_LENGTH]

class BufferPool(object):
    
    def __init__(self):
        self.sendQ = ""
        self.recvB = ""
        self.hasSent = 0
        self.hasRecv = 0
    
    def getSendQ(self):
        return self.sendQ

    def reset(self):
        self.hasSent = 0

    def setSendQ(self, num):
        self.sendQ = self.sendQ[num:]

    def setRecvB(self, message):
        self.recvB += message

    def getRecvB(self):
        return self.recvB

    def clearR(self):
        self.hasRecv = 0

    def sendM(self, message):
        self.sendQ += pad_message(message)

    def recvM(self, message):
        self.recvB += message
 
class Channel(object):
    def __init__(self, name):
        self.name = name
        self.members = []

    def getName(self):
        return self.name

    def getMembers(self):
        return self.members

    def addMember(self, sock):
        self.members.append(sock)

    def removeMember(self, sock):
        self.members.remove(sock)

class Server(object):
    def __init__(self, port):
        self.port = port
        self.server = socket.socket()
        self.channels = {}
        self.chatter = {}
        self.socketList = []
        self.buffer = {} # sock : bufferPool
        self.sendBuffer = []
        self.recvBuffer = [] # incompleted recv socket

    def run(self):
        # run the server and listen income connections # 

        self.server.bind(("localhost", self.port))
        self.server.listen(5)
        self.socketList.append(self.server)

        while True:
            readList, writeList, errorList = select.select(self.socketList,\
                                                           [], [], 0)
            for sock in readList:
                if sock == self.server:
                    (new_socket, address) = self.server.accept()
                    self.socketList.append(new_socket)
                    self.chatter[new_socket] = [None, None]
                    self.buffer[new_socket] = BufferPool()
                else:
                    message = self.recvMessage(sock)
                    #message = sock.recv(200)
                    if message:
                        if message == -10:
                            pass
                        elif self.__isCommand(message):
                            print "1"
                            note = self.commandHandler(sock, message)
                            if note:
                                self.sendMessage(sock, pad_message(note))
                        else:
                            print "2"
                            self.messageHandler(sock, message)
                    else:
                        if sock in self.socketList:
                            message = SERVER_CLIENT_LEFT_CHANNEL.format(self.chatter[sock][0])
                            self.messageHandler(sock, message)
                            channel = self.chatter[sock][1]
                            channel.removeMember(sock)
                            self.socketList.remove(sock)
                            if sock in self.recvBuffer:
                                self.recvBuffer.remove(sock)

            for sock in self.recvBuffer:
                print "hello"
                message = self.recvMessage(sock)
                if message == -10:
                    pass
                elif self.__isCommand(message):
                    print "1"
                    note = self.commandHandler(sock, message)
                    if note:
                        self.sendMessage(sock, pad_message(note))
                else:
                    print "2"
                    self.messageHandler(sock, message)


            for sock in self.sendBuffer:
                self.sendMessage(sock, None)
    
    def recvMessage(self, sock):
        if not sock in self.recvBuffer:
            self.recvBuffer.append(sock)
        
        buf = self.buffer[sock]

        message = sock.recv(MESSAGE_LENGTH - buf.hasRecv)
        print "the message is " + message + str(len(message))
        if not message:
            return message
        else:
            buf.setRecvB(message)
            buf.hasRecv += len(message)
            if buf.hasRecv == MESSAGE_LENGTH:
                tmp = buf.getRecvB()
                buf.clearR()
                buf.recvB = ""
                self.recvBuffer.remove(sock)
                return tmp.rstrip(" ")
            elif buf.hasRecv > MESSAGE_LENGTH:
                tmp = buf.getRecvB()[:MESSAGE_LENGTH]
                buf.hasRecv = buf.hasRecv - MESSAGE_LENGTH
                buf.recvB = bug.getRecvB()[MESSAGE_LENGTH:]
                return tmp.rstrip(" ")
            else:
                return -10
                
            


    def sendMessage(self, sock, message):
        # if message is None, then continue incompleted work
        # if message is presented, append the message to sock's sendQ
        buf = self.buffer[sock]
        if message == None:
            byte = sock.send(buf.getSendQ())
            if buf.hasSent + byte > MESSAGE_LENGTH:
                buf.reset()
                extra = buf.hasSent + byte - MESSAGE_LENGTH
                buf.hasSent += extra
            else:
                buf.hasSent += byte
            buf.setSendQ(byte)
            if buf.hasSent == MESSAGE_LENGTH:
            # has sent a complete message, update followings
                buf.reset()
                if len(buf.getSendQ()) == 0:
                    self.sendBuffer.remove(sock)
        else:
            buf.sendM(message)
            if not sock in self.sendBuffer:
                self.sendBuffer.append(sock)
            self.sendMessage(sock, None)


    def __isCommand(self, message):
        message = message.strip(" ")
        return message[0] == '/'


    def commandHandler(self, sock, message):
        message = message.strip(" ").split()
        if message[0] == "/join":
            if len(message) < 2:
                note = SERVER_JOIN_REQUIRES_ARGUMENT
                self.sendMessage(sock, pad_message(note))
            else:
                self.joinChannel(sock, message[1])
        elif message[0] == "/create":
            if len(message) < 2:
                note = SERVER_CREATE_REQUIRES_ARGUMENT
                self.sendMessage(sock, pad_message(note))
            else:
                if message[1] in self.channels:
                    note = SERVER_CHANNEL_EXISTS.format(message[1])
                    self.sendMessage(sock, pad_message(note))
                else:
                    self.createChannel(sock, message[1])
        elif message[0] == "/list":
            print "error"
            self.listChannel(sock)
        else:
            return SERVER_INVALID_CONTROL_MESSAGE.format(message)

    def listChannel(self, sock):
        output = ""
        for key in self.channels:
            output += self.channels[key].getName() + '\n'
        if output:
            self.sendMessage(sock, pad_message(output[:-1]))
        
    
    def joinChannel(self, sock, name):
        try:
            channel = self.channels[name]
        except:
            note = SERVER_NO_CHANNEL_EXISTS.format(name)
            #print self.chatter[sock][0]
            self.sendMessage(sock, pad_message(note))
            return 
        oldChannel = self.chatter[sock][1]
        if oldChannel:
            oldChannel.removeMember(sock)
        channel.addMember(sock)
        self.chatter[sock][1] = channel
        note = SERVER_CLIENT_JOINED_CHANNEL.format(self.chatter[sock][0])
        for member in channel.getMembers():
            if member != sock:
                self.sendMessage(member, pad_message(note))
        #print("socket name: {0}, channel name: {1}".format(self.chatter[sock][0],
        #                                                self.chatter[sock][1].getName()))
        #print("channel mamebers: " + str(self.chatter[sock][1].getMembers()))


    def createChannel(self, sock, name):
        channel = Channel(name)
        self.channels[name] = channel
        
        # check if current sock in any channel

        oldChannel = self.chatter[sock][1]
        if oldChannel:
            oldChannel.removeMember(sock)
            for member in oldChannel.getMembers():
                message = SERVER_CLIENT_LEFT_CHANNEL.format(self.chatter[sock][0])
                self.sendMessage(member, pad_message(message))
        channel.addMember(sock)
        self.chatter[sock][1] = channel
        
        #print("socket name: {0}, channel name: {1}".format(self.chatter[sock][0],
        #                                                   self.chatter[sock][1].getName()))

    def messageHandler(self, sock, message):
        # first update chatter's name
        if self.chatter[sock][0] == None:
            message = message.rstrip(" ")
            self.chatter[sock][0] = message
            #print (self.chatter[sock])
        elif self.chatter[sock][1] == None:
            note = SERVER_CLIENT_NOT_IN_CHANNEL
            self.sendMessage(sock, pad_message(note))
        else:
            channel = self.chatter[sock][1]
            members = channel.getMembers()
            for socket in members:
                if self.server and socket != sock:
                    tmp = "[" + str(self.chatter[sock][0]) + "]" + " " + message
                    self.sendMessage(socket, pad_message(tmp))

if __name__ == "__main__":
    port = int(sys.argv[1])
    server = Server(port)
    server.run()
