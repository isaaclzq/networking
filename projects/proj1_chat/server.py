import socket
import select
import sys

MESSAGE_LENGTH = 200

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
                            self.commandHandler(sock, message)
                        else:
                            self.messageHandler(sock, message)
                    else:
                        pass
    
    def __isCommand(self, message):
        message = message.lstrip(" ")
        return message[0] == '/'


    def commandHandler(self, sock, message):
        message = message.strip(" ").split()
        if message[0] == "/join":
            self.joinChannel(sock, message[1])
        elif message[0] == "/create":
            self.createChannel(sock, message[1])
        elif message[0] == "/list":
            self.listChannel()
        else:
            print("No Such Command")

    def listChannel(self):
        for key in self.channels:
            print(self.channels[key].getName())
    
    def joinChannel(self, sock, name):
        channel = self.channels[name]
        if not channel:
            print("channel does not exist")
        else:
            oldChannel = self.chatter[sock][1]
            if oldChannel:
                oldChannel.removeMember(sock)
            channel.addMember(sock)
            self.chatter[sock][1] = channel
            print("socket name: {0}, channel name: {1}".format(self.chatter[sock][0],
                                                        self.chatter[sock][1].getName()))
            print("channel mamebers: " + str(self.chatter[sock][1].getMembers()))


    def createChannel(self, sock, name):
        channel = Channel(name)
        self.channels[name] = channel
        
        # check if current sock in any channel

        oldChannel = self.chatter[sock][1]
        if oldChannel:
            oldChannel.removeMember(sock)
        channel.addMember(sock)
        self.chatter[sock][1] = channel

        print("socket name: {0}, channel name: {1}".format(self.chatter[sock][0],
                                                           self.chatter[sock][1].getName()))

    def messageHandler(self, sock, message):
        # first update chatter's name
        if self.chatter[sock][0] == None:
            message = message.rstrip(" ")
            self.chatter[sock][0] = message
            print (self.chatter[sock])
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
