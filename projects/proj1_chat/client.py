import socket
import sys 
import select

MESSAGE_LENGTH = 200

def pad_message(message):
    while len(message) < MESSAGE_LENGTH:
        message += " "
    return message[:MESSAGE_LENGTH]



class Client(object):

    def __init__(self, name, addr, port):
        self.addr = addr
        self.port = port
        self.name = name
        self.client = socket.socket()

    def run(self):
        self.client.connect((self.addr, self.port))
        self.client.sendall(pad_message(self.name))

        while True:
            socketList = [sys.stdin, self.client]
            readList, writeList, errorList = select.select(socketList, [], [], 0)
            
            for sock in readList:
                if sock == self.client:
                    message = sock.recv(MESSAGE_LENGTH)
                    if message:
                        sys.stdout.write(message)
                else:
                    msg = sys.stdin.readline()
                    self.client.sendall(msg)


    def sendMessage(self, message):
        self.client.sendall(message)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("the input length is not long enough")
        sys.exit()

    name = sys.argv[1]
    addr = sys.argv[2]
    port = int(sys.argv[3])
    
    cli = Client(name, addr, port)
    cli.run()
    #message = sys.stdin.readline()
    #cli.sendMessage(message)
    

