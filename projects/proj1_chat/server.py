import socket
import select
import sys
from utils import *

def pad_message(message):
    while len(message) < MESSAGE_LENGTH:
        message += " "
    return message[:MESSAGE_LENGTH]

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
                else:
                    message = sock.recv(MESSAGE_LENGTH)
                    if message:
                        if self.__isCommand(message):
                            note = self.commandHandler(sock, message)
                            if note:
                                sock.sendall(pad_message(note))
                        else:
                            self.messageHandler(sock, message)
                    else:
                        if sock in self.socketList:
                            message = SERVER_CLIENT_LEFT_CHANNEL.format(self.chatter[sock][0])
                            self.messageHandler(sock, message)
                            channel = self.chatter[sock][1]
                            channel.removeMember(sock)
                            self.socketList.remove(sock)

    
    def recvMsg(self, sock):
        cache = ""
        while len(output) < MESSAGE_LENGTH:
            


    def __isCommand(self, message):
        message = message.lstrip(" ")
        return message[0] == '/'


    def commandHandler(self, sock, message):
        message = message.strip(" ").split()
        if message[0] == "/join":
            if len(message) < 2:
                note = SERVER_JOIN_REQUIRES_ARGUMENT
                sock.sendall(note)
            else:
                self.joinChannel(sock, message[1])
        elif message[0] == "/create":
            if len(message) < 2:
                note = SERVER_CREATE_REQUIRES_ARGUMENT
                sock.sendall(note)
            else:
                if message[1] in self.channels:
                    note = SERVER_CHANNEL_EXISTS.format(message[1])
                    sock.sendall(note)
                else:
                    self.createChannel(sock, message[1])
        elif message[0] == "/list":
            self.listChannel(sock)
        else:
            return SERVER_INVALID_CONTROL_MESSAGE.format(message)

    def listChannel(self, sock):
        output = ""
        for key in self.channels:
            output += self.channels[key].getName() + '\n'
        sock.sendall(output[:-1])

    
    def joinChannel(self, sock, name):
        try:
            channel = self.channels[name]
        except:
            note = SERVER_NO_CHANNEL_EXISTS.format(name)
            #print self.chatter[sock][0]
            sock.sendall(note)
            return 
        oldChannel = self.chatter[sock][1]
        if oldChannel:
            oldChannel.removeMember(sock)
        channel.addMember(sock)
        self.chatter[sock][1] = channel
        note = SERVER_CLIENT_JOINED_CHANNEL.format(self.chatter[sock][0])
        for member in channel.getMembers():
            if member != sock:
                member.sendall(note)
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
            sock.sendall(note)
        else:
            channel = self.chatter[sock][1]
            members = channel.getMembers()
            for socket in members:
                if socket != self.server and socket != sock:
                    message = "[" + str(self.chatter[sock][0]) + "]" + " " + message
                    socket.sendall(message)

if __name__ == "__main__":
    port = int(sys.argv[1])
    server = Server(port)
    server.run()
