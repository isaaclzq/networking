import socket
import sys 
import select
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

class Client(object):

    def __init__(self, name, addr, port):
        self.addr = addr
        self.port = int(port)
        self.name = name
        self.client = socket.socket()
        self.buffer = {} # sock : bufferPool
        self.recvBuffer = []
        self.sendBuffer = [] # sendBuffer socket

    def run(self):
        try:
            self.client.connect((self.addr, self.port))
        except:
            print (CLIENT_CANNOT_CONNECT.format(self.addr, self.port))
            self.client.close()
            sys.exit()
        self.buffer[sys.stdin] = BufferPool()
        self.buffer[self.client] = BufferPool()
        self.sendMessage(self.client, self.name)
        sys.stdout.write(CLIENT_MESSAGE_PREFIX)
        sys.stdout.flush()
        socketList = [sys.stdin, self.client]
        
        while True:
            readList, writeList, errorList = select.select(socketList, [], [], 0)
            for sock in readList:
                if sock == self.client:
                    #message = sock.recv(200)
                    message = self.recvMessage(sock)
                    if message:
                        if message == -10:
                            pass
                        else:
                            sys.stdout.write(CLIENT_WIPE_ME + '\r' + message.rstrip(" ")+"\n")
                            sys.stdout.flush()
                            sys.stdout.write(CLIENT_MESSAGE_PREFIX)
                            sys.stdout.flush()
                    else:
                        print (CLIENT_WIPE_ME + '\r' + CLIENT_SERVER_DISCONNECTED.format(self.addr, self.port))
                        self.client.close()
                        sys.exit()
                else:
                    msg = sys.stdin.readline()
                    self.sendMessage(self.client, msg[:-1])
                    sys.stdout.write("[Me] ")
                    sys.stdout.flush()

            for sock in self.recvBuffer:
                self.recvMessage(sock)

            for sock in self.sendBuffer:
                self.sendMessage(sock, None)

    def recvMessage(self, sock):
        if not sock in self.recvBuffer:
            self.recvBuffer.append(sock)
        
        buf = self.buffer[sock]

        message = sock.recv(MESSAGE_LENGTH - buf.hasRecv)
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
        # if message is None, then continue sendBuffer work
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

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("the input length is not long enough")
        sys.exit()

    name = sys.argv[1]
    addr = sys.argv[2]
    port = sys.argv[3]
    
    cli = Client(name, addr, port)
    cli.run()
    

