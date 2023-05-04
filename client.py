import socket
import threading
import sys

from os import _exit
from sys import stdout
from time import sleep

def lamportSort(pair):
    return (-pair[0], -pair[1])

def mutexRequest(originalLamport):
    sleep(3)
    print("Requesting <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)
    #lamportClock += 1
    for client in outboundSOCKETS.values():
        client.sendall(bytes(str(clientNum) + " request " + str(originalLamport), "utf-8"))
        # print("Request sent to client " + str(client), flush=True)
        sleep(1)

def mutexRelease(originalLamport):
    sleep(3)
    #lamportClock += 1
    print("Releasing <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)
    for client in outboundSOCKETS.values():
        client.sendall(bytes(str(clientNum) + " release " + str(lamportClock) + " " + str(originalLamport), "utf-8"))
       #  print("Release sent to client " + str(client), flush=True)
        sleep(1)

# keep waiting and asking for user inputs
def get_user_input():
    while True:
        user_input = input()                             # wait for user input
        waitFunc = user_input.split(" ")
    
        if user_input == "exit":                         # exit safely
            out_sock.close()                             # close socket before exiting
            stdout.flush()                               # flush console output buffer in case of remaining prints that havent printed
            _exit(0)                                     # exit program with status 0
        
        if waitFunc[0] == "wait":                      # wait function for client
            sleepNum = waitFunc[1]
            sleep(int(sleepNum))

        else: 
            if waitFunc[0] == "Transfer":
                transferTarget = waitFunc[1]
                transferTarget = transferTarget.strip("P")

                global lamportClock
                lamportClock += 1

                originalLamport = lamportClock

                print("Request <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)

                queue.append((lamportClock, int(clientNum)))
                queue.sort(key=lamportSort)

                mutexRequest(originalLamport)
                timeoutCount = 0
                while (ReplyArr[0] != 1 and ReplyArr[1] != 1) or (ReplyArr[0] != 1 and ReplyArr[2] != 1) or (ReplyArr[1] != 1 and ReplyArr[2] != 1):
                    timeoutCount += 1
                    sleep(1)
                    if timeoutCount == 9:
                        print("Timeout.")
                        break
                    continue
                
                print("QUEUE: " , str(queue))
                
                while(queue[0][0] != int(lamportClock)) and (queue[0][1] != int(clientNum)):
                    # print("queue[0][0]: " + str(queue[0][0]) + " lamportClock: " + str(lamportClock) + " queue[0][1]: " + str(queue[0][1]) + " transferTarget: " + str(transferTarget))
                    continue
                
                out_sock.sendall(bytes(user_input + " <" + str(originalLamport) + "," + str(clientNum) + ">", "utf-8"))
                lamportClock += 1

                queue.pop(0)
                ReplyArr[0] = 0
                ReplyArr[1] = 0
                ReplyArr[2] = 0

                lamportClock += 1
                mutexRelease(originalLamport)

            if waitFunc[0] == "Balance":
                out_sock.sendall(bytes(user_input, "utf-8"))
                lamportClock += 1

            else:
                try:
                    out_sock.sendall(bytes(user_input, "utf-8"))                   # send user input string to server, converted into bytes
                except:                                                            # handling exception in case trying to send data to a closed connection
                    print("Exception in sending to server")
                continue

# simulates network delay then handles received message
def handle_msg(data):
    sleep(3)                                # simulate 3 seconds message-passing delay
    data = data.decode()                    # decode byte data into a string
    print(data)                             # echo message to console

def getConnections():
    while True:                              # while loop to make new connections
        try:
            conn, addr = CLIENT_SOCKET.accept()
        except:
            print("Exception in accepting new connection")
            break
        CLIENT_SOCKETS.append((conn, addr))
        print("New connection from inbound client", flush=True)

        threading.Thread(target=listenForClients, args=(conn,addr)).start()

def respond(data):                            # handle a new connection by waiting to receive from connection
    global lamportClock
    data = data.decode()
    data = data.split(" ")

    incomingID = int(data[0])
    print("Incoming ID: " + str(incomingID), flush=True)

    msg = data[1]
    incomingLamport = int(data[2])

    if msg == "request":
        lamportClock = 1 + max(lamportClock, incomingLamport)

        queue.append((incomingLamport, incomingID))
        queue.sort(key=lamportSort)

        lamportClock += 1

        print("Replying to request <" + str(incomingLamport) + "," + str(incomingID) + ">", flush=True)
        outboundSOCKETS[incomingID].sendall(bytes(str(clientNum) + " reply " + str(lamportClock) + " " + str(incomingLamport), "utf-8"))

    if msg == "reply":
        incomingLamport = int(data[3])
        lamportClock = 1 + max(lamportClock, incomingLamport)
        print ("Client P" + str(incomingID) + " replied <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)
        ReplyArr[incomingID - 1] = 1
        
    if msg == "release":
        incomingLamport = int(data[3])
        lamportClock = 1 + max(lamportClock, incomingLamport)
        print("Client P" + str(incomingID) + " released <" + str(incomingLamport) + "," + str(clientNum) + ">", flush=True)
        queue.pop(0)
    
def listenForClients(conn, addr):
    while True:
        try:
            data = conn.recv(1024)
        except:
            print(f"exception in receiving from {addr[1]}", flush=True)
            break

        if not data:
            conn.close()
            print(f"connection closed from {addr[1]}", flush=True)
            break
        
        threading.Thread(target=respond, args=(data,)).start()


if __name__ == "__main__":
    sleep(1)                                # decode byte data into a string
    queue = []
    lamportClock = 0
    ReplyArr = [0,0,0]

    # ------------------ server socket setup ------------------ #
    SERVER_IP = socket.gethostname()
    SERVER_PORT = 9000

    pid = str(sys.argv[1])
    out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # create a socket object, SOCK_STREAM specifies a TCP socket
    out_sock.connect((SERVER_IP, SERVER_PORT))                      # attempt to connect own socket to server's socket address
    print("Client " + pid + " has connected to the server.", flush=True)
    out_sock.sendall(bytes(pid, "utf-8"))

    #-----------------------------------------------------------#
        
    #----------- get client number from command line argument ------------#
    clientNum = str(sys.argv[1])                                    # get client number from command line argument
    clientNum = clientNum[-1]                                       # get last digit of client number
    CLIENT_PORT = int(clientNum) + 9000                             # client port is 9001 for client 1, 9002 for client 2, etc.
    #---------------------------------------------------------------------#

    #---------------------- client socket setup ----------------------#
    CLIENT_IP = socket.gethostname()
    CLIENT_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # create a socket object, SOCK_STREAM specifies a TCP socket
    CLIENT_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    CLIENT_SOCKET.bind((CLIENT_IP, CLIENT_PORT))                            # bind socket to address
    CLIENT_SOCKET.listen()                                                  # start listening for connections to the address
    CLIENT_SOCKETS = []                                                     # container to store all connections

    #-----------------------------------------------------------------#

    threading.Thread(target=getConnections).start()

    # ------------------ outbound socket setup ------------------ #
    sleep(5)
    outboundSOCKETS = {}
    outBoundSocketA = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a socket object, SOCK_STREAM specifies a TCP socket
    outBoundSocketB = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a socket object, SOCK_STREAM specifies a TCP socket

    #-------------------------------------------------------------#

    #----------- bind sockets using port number ------------#
    if clientNum == "1":
        outBoundSocketA.connect((SERVER_IP, 9002))
        outboundSOCKETS[2] = outBoundSocketA
        print("Connected to client P2", flush=True)
        
        outBoundSocketB.connect((SERVER_IP, 9003))
        outboundSOCKETS[3] = outBoundSocketB
        print("Connected to client P3", flush=True)

    if clientNum == "2":
        outBoundSocketA.connect((SERVER_IP, 9001))
        outboundSOCKETS[1] = outBoundSocketA
        print("Connected to client P1", flush=True)
        
        outBoundSocketB.connect((SERVER_IP, 9003))
        outboundSOCKETS[3] = outBoundSocketB
        print("Connected to client P3", flush=True)
    
    if clientNum == "3":
        outBoundSocketA.connect((SERVER_IP, 9001))
        outboundSOCKETS[1] = outBoundSocketA
        print("Connected to client P1", flush=True)
        
        outBoundSocketB.connect((SERVER_IP, 9002))
        outboundSOCKETS[2] = outBoundSocketB
        print("Connected to client P2", flush=True)
    #-------------------------------------------------------#

    threading.Thread(target=get_user_input).start()

    while True:
        try:
            data = out_sock.recv(1024)

        except:
            print("Exception in receiving")
            break
        if not data:
            out_sock.close()
            print("Connection closed from server")
            break

    threading.Thread(target=handle_msg, args=(data,)).start()

