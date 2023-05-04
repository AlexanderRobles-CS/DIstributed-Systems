import socket
import threading
import sys

from os import _exit
from sys import stdout
from time import sleep

def lampQueue(pair):            #function to help fix the lamport clock to queue them correctly
    return (-pair[0], -pair[1]) #sorts by lamport clock, then by client number


# simulates network delay then handles received message
def handle_msg(data):
    sleep(3)                                # simulate 3 seconds message-passing delay
    data = data.decode()                    # decode byte data into a string
    print(data)                             # echo message to console


def mutexReq(originalLamport):                                                               #function to send request to all clients
    sleep(3)                                                                                 #sleep for 3 seconds to simulate the time it takes to send the request
    #lamportClock += 1                                                                       #increment the lamport clock             
    print("REQUEST <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)         #print the request and the lamport clock
    for client in outboundSOCKETS.values():                                                  #for each client in the outbound sockets
        client.sendall(bytes(str(clientNum) + " request " + str(originalLamport), "utf-8"))  #send the request to the client
        # print("Request sent to client " + str(client), flush=True)
        sleep(1)                                                                             #sleep for 1 second


def mutexRel(originalLamport):
    sleep(3)                                                                                                            #sleep for 3 seconds to simulate the time it takes to send the release
    #lamportClock += 1                                                                                                  #increment the lamport clock              
    print("RELEASE <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)                                    #print the release and the lamport clock
    for client in outboundSOCKETS.values():                                                                             #for each client in the outbound sockets
        client.sendall(bytes(str(clientNum) + " release " + str(lamportClock) + " " + str(originalLamport), "utf-8"))   #send the release to the client
       #  print("Release sent to client " + str(client), flush=True)
        print("DONE <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)                                   #print the done and the lamport clock
        sleep(1)                                                                                                        #sleep for 1 second
    

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
            if waitFunc[0] == "Transfer":                                 #if the user input is a transfer
                transferTarget = waitFunc[1]                              #set transfer target to the second word in the user input to get the client number
                transferTarget = transferTarget.strip("P")                #strip the P from the transfer target so we only have the number

                global lamportClock                                        #global variable for the lamport clock
                lamportClock += 1                                          #increment the lamport clock

                originalLamport = lamportClock                             #save the original lamport clock

                print("REQUEST <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)     #print the request and the lamport clock as designated in the instructions

                mutexQueue.append((lamportClock, int(clientNum)))          #append the lamport clock and the client number to the mutex queue
                mutexQueue.sort(key=lampQueue)                             #sort the mutex queue by the lamport clock and the client number

                mutexReq(originalLamport)                                  #call the mutex request function with the original lamport clock value
                

                #while loop to allow for timeout in case of client failure
                timeoutVal = 0                                             #set the timeout value to 0
                while (ReplyArr[0] != 1 and ReplyArr[1] != 1) or (ReplyArr[0] != 1 and ReplyArr[2] != 1) or (ReplyArr[1] != 1 and ReplyArr[2] != 1):
                    timeoutVal += 1                                #increment the timeout value
                    sleep(1)                                       #sleep for 1 second
                    if timeoutVal == 9:                            #if the timeout value reaches 9
                        print("INCORRECT")                         #print incorrect       
                        break                                      #break out of the loop
                    continue
                
                print("QUEUE: " , str(mutexQueue))                 #print the mutex queue
                
                #while loop to wait until the mutex queue head is the same as the current client
                while(mutexQueue[0][0] != int(lamportClock)) and (mutexQueue[0][1] != int(clientNum)):  #while the lamport clock and client number in the mutex queue are not equal to the lamport clock and client number
                    # print("mutexQueue[0][0]: " + str(mutexQueue[0][0]) + " lamportClock: " + str(lamportClock) + " mutexQueue[0][1]: " + str(mutexQueue[0][1]) + " transferTarget: " + str(transferTarget))
                    continue
                
                out_sock.sendall(bytes(user_input + " <" + str(originalLamport) + "," + str(clientNum) + ">", "utf-8")) #send the user input to the server with the original lamport clock and client number
                lamportClock += 1                                                                                      #increment the lamport clock

                mutexQueue.pop(0)                                                                                   #pop the head of the mutex queue
                #reset the reply array so the replies can be counted again for a new transaction
                ReplyArr[0] = 0                                                                                     #set the reply[0] array to 0
                ReplyArr[1] = 0                                                                                     #set the reply[1] array to 0
                ReplyArr[2] = 0                                                                                     #set the reply[2] array to 0

                lamportClock += 1                                                                                   #increment the lamport clock
                mutexRel(originalLamport)                                                                           #call the mutex release function with the original lamport clock value

                print("SUCCESS")                                                                                    #print success for a successful transaction

            if waitFunc[0] == "Balance":                                                #if the user input is a balance
                out_sock.sendall(bytes(user_input, "utf-8"))                            #send the user input to the server
                lamportClock += 1                                                       #increment the lamport clock

            else:
                try:
                    out_sock.sendall(bytes(user_input, "utf-8"))                   # send user input string to server, converted into bytes
                except:                                                            # handling exception in case trying to send data to a closed connection
                    print("Exception in sending to server")
                continue


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

        mutexQueue.append((incomingLamport, incomingID))
        mutexQueue.sort(key=lampQueue)

        lamportClock += 1

        print("Replying to request <" + str(incomingLamport) + "," + str(incomingID) + ">", flush=True)
        outboundSOCKETS[incomingID].sendall(bytes(str(clientNum) + " reply " + str(lamportClock) + " " + str(incomingLamport), "utf-8"))

    if msg == "reply":
        incomingLamport = int(data[3])
        lamportClock = 1 + max(lamportClock, incomingLamport)
        print ("Client P" + str(incomingID) + " REPLIED <" + str(lamportClock) + ", " + str(clientNum) + ">", flush=True)
        ReplyArr[incomingID - 1] = 1
        
    if msg == "release":
        incomingLamport = int(data[3])
        lamportClock = 1 + max(lamportClock, incomingLamport)
        print("Client P" + str(incomingID) + " released <" + str(incomingLamport) + "," + str(clientNum) + ">", flush=True)
        mutexQueue.pop(0)
    

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
    sleep(1)                                # sleep for 1 second to allow server to start up
    mutexQueue = []                         # initialize queue for mutex
    lamportClock = 0                        # initialize lamport clock
    ReplyArr = [0,0,0]                      # initialize reply array

    # ------------------ server socket setup ------------------ #
    SERVER_IP = socket.gethostname()        # get server IP address
    SERVER_PORT = 9000                      # server port set to 9000

    pid = str(sys.argv[1])                                          #set pid to command line argument
    out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # create a socket object, SOCK_STREAM specifies a TCP socket
    out_sock.connect((SERVER_IP, SERVER_PORT))                      # attempt to connect own socket to server's socket address
    print("Client " + pid + " has connected to the server.", flush=True)    # print confirmation of connection to server
    out_sock.sendall(bytes(pid, "utf-8"))                                   # send pid to server

    #-----------------------------------------------------------#
        
    #----------- get client number from command line argument ------------#
    clientNum = str(sys.argv[1])                                    # get client number from command line argument
    clientNum = clientNum[-1]                                       # get last digit of client number
    CLIENT_PORT = int(clientNum) + 9000                             # client port is 9001 for client 1, 9002 for client 2, etc.
    #---------------------------------------------------------------------#

    #---------------------- client socket setup ----------------------#
    CLIENT_IP = socket.gethostname()                                        # get client IP address
    CLIENT_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # create a socket object, SOCK_STREAM specifies a TCP socket
    CLIENT_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)     # set socket option to allow reuse of address
    CLIENT_SOCKET.bind((CLIENT_IP, CLIENT_PORT))                            # bind socket to address
    CLIENT_SOCKET.listen()                                                  # start listening for connections to the address
    CLIENT_SOCKETS = []                                                     # container to store all connections

    #-----------------------------------------------------------------#

    threading.Thread(target=getConnections).start()                         # start thread to listen for new connections

    # ------------------ outbound socket setup ------------------ #
    sleep(5)                                                            # sleep for 5 seconds to allow all clients to connect to server
    outboundSOCKETS = {}                                                # create dictionary to store outbound sockets
    outBoundSocketA = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a socket object, SOCK_STREAM specifies a TCP socket
    outBoundSocketB = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # create a socket object, SOCK_STREAM specifies a TCP socket

    #-------------------------------------------------------------#

    #----------- bind sockets using port number ------------#
    if clientNum == "1":                                # if client number is 1
        outBoundSocketA.connect((SERVER_IP, 9002))      # connect to client 2 with port number 9002
        outboundSOCKETS[2] = outBoundSocketA            # store socket in dictionary with key 2
        print("Connected to client P2", flush=True)     # print confirmation of connection to client 2
        
        outBoundSocketB.connect((SERVER_IP, 9003))      # connect to client 3 with port number 9003
        outboundSOCKETS[3] = outBoundSocketB            # store socket in dictionary with key 3
        print("Connected to client P3", flush=True)     # print confirmation of connection to client 3

    if clientNum == "2":                                # if client number is 2
        outBoundSocketA.connect((SERVER_IP, 9001))      # connect to client 1 with port number 9001
        outboundSOCKETS[1] = outBoundSocketA            # store socket in dictionary with key 1
        print("Connected to client P1", flush=True)     # print confirmation of connection to client 1
        
        outBoundSocketB.connect((SERVER_IP, 9003))      # connect to client 3 with port number 9003
        outboundSOCKETS[3] = outBoundSocketB            # store socket in dictionary with key 3
        print("Connected to client P3", flush=True)     # print confirmation of connection to client 3
    
    if clientNum == "3":                                # if client number is 3
        outBoundSocketA.connect((SERVER_IP, 9001))      # connect to client 1 with port number 9001
        outboundSOCKETS[1] = outBoundSocketA            # store socket in dictionary with key 1
        print("Connected to client P1", flush=True)     # print confirmation of connection to client 1
        
        outBoundSocketB.connect((SERVER_IP, 9002))      # connect to client 2 with port number 9002
        outboundSOCKETS[2] = outBoundSocketB            # store socket in dictionary with key 2
        print("Connected to client P2", flush=True)     # print confirmation of connection to client 2
    #-------------------------------------------------------#

    threading.Thread(target=get_user_input).start()     # start thread to get user input

    while True:                                         # loop to listen for incoming messages
        try:
            data = out_sock.recv(1024)                  # receive data from server

        except:
            print("Exception in receiving")             # print exception message
            break
        if not data:                                    # if no data is received
            out_sock.close()                            # close socket
            print("Connection closed from server")      # print confirmation of connection to server
            break

    threading.Thread(target=handle_msg, args=(data,)).start()   # start thread to handle incoming message

