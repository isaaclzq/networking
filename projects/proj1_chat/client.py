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

    def getSendQLen(self):
        return len(self.sendQ)
    
    def getRecvBLen(self):
        return len(self.recvB)

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
        self.incompleted = [] # incompleted socket

    def run(self):
        try:
            self.client.connect((self.addr, self.port))
        except:
            print (CLIENT_CANNOT_CONNECT.format(self.addr, self.port))
            self.client.close()
            sys.exit()
        sendMessage(self.name)
        sys.stdout.write("[Me] ")
        sys.stdout.flush()
        socketList = [sys.stdin, self.client]
        self.buffer[sys.stdin] = BufferPool()
        self.buffer[self.client] = BufferPool()

        while True:
            readList, writeList, errorList = select.select(socketList, [], [], 0)
            for sock in readList:
                if sock == self.client:
                    message = sock.recv(MESSAGE_LENGTH)
                    if message:
                        sys.stdout.write(CLIENT_WIPE_ME + '\r' + message.rstrip(" ")+'\n')
                        sys.stdout.flush()
                        sys.stdout.write("[Me] ")
                        sys.stdout.flush()
                    else:
                        print (CLIENT_WIPE_ME + '\r' + CLIENT_SERVER_DISCONNECTED.format(self.addr, self.port))
                        self.client.close()
                        sys.exit()
                else:
                    msg = sys.stdin.readline()
                    sendMessage(msg)
                    sys.stdout.write("[Me] ")
                    sys.stdout.flush()


    def sendMessage(self, sock, message):
        # if message is None, then continue incompleted work
        # if message is presented, append the message to sock's sendQ

        buf = self.bufferPool[sock]
        if message == None:
            byte = sock.send(MESSAGE_LENGTH - buf.hasSent)
            buf.hasSent += byte
            if buf.hasSent == MESSAGE_LENGTH:
            # has sent a complete message, update followings
                pass 
        else:
            buf.sendM(message)
            if not sock in self.incompleted:
                self.incompleted.append(sock)

    def RecvMessage(self, sock, message):
        pass

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("the input length is not long enough")
        sys.exit()

    name = sys.argv[1]
    addr = sys.argv[2]
    port = sys.argv[3]
    
    cli = Client(name, addr, port)
    cli.run()
    

