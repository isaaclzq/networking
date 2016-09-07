import socket
import sys 
import select
from utils import *

def pad_message(message):
    while len(message) < MESSAGE_LENGTH:
        message += " "
    return message[:MESSAGE_LENGTH]



class Client(object):

    def __init__(self, name, addr, port):
        self.addr = addr
        self.port = int(port)
        self.name = name
        self.client = socket.socket()

    def run(self):
        try:
            self.client.connect((self.addr, self.port))
        except:
            print (CLIENT_CANNOT_CONNECT.format(self.addr, self.port))
            self.client.close()
            sys.exit()
        self.client.sendall(pad_message(self.name))
        sys.stdout.write("[Me] ")
        sys.stdout.flush()
        socketList = [sys.stdin, self.client]

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
                    self.client.sendall(msg)
                    sys.stdout.write("[Me] ")
                    sys.stdout.flush()


    def sendMessage(self, message):
        self.client.sendall(message)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("the input length is not long enough")
        sys.exit()

    name = sys.argv[1]
    addr = sys.argv[2]
    port = sys.argv[3]
    
    cli = Client(name, addr, port)
    cli.run()
    

