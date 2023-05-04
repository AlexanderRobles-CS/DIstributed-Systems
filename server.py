# server.py
# this process accepts an arbitrary number of client connections
# it echoes any message received from any client to console
# then broadcasts the message to all clients
import blockchain
import socket
import threading

from os import _exit
from sys import stdout
from time import sleep
from blockchain import Blockchain, Block

def get_userInput():
        
    while True:
        userInput = input()                     # wait for user input
        waitFunc = userInput.split(" ")

        if userInput == "exit":
            in_sock.close()                         # close all sockets before exiting
            for sock in out_socks:
                sock[0].close()
            print("exiting program", flush=True)
            stdout.flush()                          # flush console output buffer in case there are remaining prints
            _exit(0)                                # exit program with status 0

        elif userInput == "Blockchain":             # iterate through blockchain to append to history array
            history = []
            for block in blockchain.chain:
                print("Nonce: " + str(block.nonce))
                history.append("(" + str(block.sender) + ", " + str(block.receiver) + ", $" + str(block.amount) + ", " + 
                               str(block.nonce) + ", " + str(block.lamportClock) + ", " + str(block.prevHash) + ")") 

            if len(history) > 1:                        # extrapolate data from history if there is a history of transactions
                blockchainHistory = "["
                for hist in history[1:]:
                    blockchainHistory += hist + ", "
                blockchainHistory = blockchainHistory[:-2] + "]"

            elif len(history) == 1:                     # if there is no histroy print an empty array
                blockchainHistory = "[]"

            print(blockchainHistory)

        elif userInput == "Balance":                # get the balance of each user
            p1Balance = blockchain.getBalance("P1")
            p2Balance = blockchain.getBalance("P2")
            p3Balance = blockchain.getBalance("P3")

            print("P1: $" + str(p1Balance) + ", " + "P2: $" + str(p2Balance) + ", " +  "P3: $" + str(p3Balance))

        elif waitFunc[0] == "wait":                 # wait function used in autograder
            print("waiting " + str(waitFunc[1]) + " seconds")
            sleepNum = waitFunc[1]
            sleep(int(sleepNum))

def handle_msg(data,conn):                      # simulates network delay then handles received message
    sleep(3)
    data = data.decode()                        # decode byte data into a string
    try:
        userRequest = data.split(" ")
        if userRequest[0] == "Transfer":        # get user input for transfer
                print("received Transfer: " + userRequest[1] + " " + userRequest[2] + " " + userRequest[3])
                transferTarget = userRequest[1]
                transferAmount = userRequest[2].replace("$", "")
                
                if int(transferAmount) > blockchain.getBalance(PIDS[conn]):     # determine if there is sufficient balance
                    conn.sendall(bytes(f"Insufficient Balance", "utf-8"))       # let user know if there are sufficient funds

                else:                                                        # append block with transaction information to blockchain
                    block = Block(str(PIDS[conn]), str(transferTarget), str(transferAmount), str(blockchain.getLatestBlock().hash), userRequest[3])
                    blockchain.appendBlock(block, str(PIDS[conn]), transferTarget, transferAmount)
                    conn.sendall(bytes(f"Success", "utf-8"))

        if userRequest[0] == "Balance":                                         # get the user balance of a given user
            balance = blockchain.getBalance(userRequest[1])
            conn.sendall(bytes(f"Balance: ${balance}", "utf-8"))

    except:
        pass


def respond(conn, addr):                            # handle a new connection by waiting to receive from connection
    data = conn.recv(1024)
    data = data.decode()
    PIDS[conn] = data

    if PIDS == 3:
        print("All clients connected.", flush=True)

    while True:                                     # infinite loop to keep waiting to receive new data from this client
        try:
            data = conn.recv(1024)
        except:
            print(f"exception in receiving from {addr[1]}", flush=True)
            break
            
        if not data:                                # if client's socket closed, it will signal closing without any data
            conn.close()                            # close own socket to client since other end is closed
            print(f"connection closed from {addr[1]}", flush=True)
            break

        threading.Thread(target=handle_msg, args=(data,conn)).start()   #new thread to handle message so simulated network delay and message handling don't block receive

if __name__ == "__main__":

    PIDS = {}
    blockchain = Blockchain()                   #initalize blockchain
    IP = socket.gethostname()
    PORT = 9000
    in_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # create a socket object, SOCK_STREAM specifies a TCP socket
    in_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)   # when REUSEADDR is not set
    in_sock.bind((IP, PORT))                        # bind socket to address
    in_sock.listen()                                # start listening for connections to the address
    out_socks = []                                  # container to store all connections
    threading.Thread(target=get_userInput).start()  # new thread to wait for user input

    while True:                                     # wait to accept any incoming connections
        try:
            conn, addr = in_sock.accept()
        except:
            print("exception in accept", flush=True)
            break
        out_socks.append((conn, addr))                              # add connection to array to send data through it later
        threading.Thread(target=respond, args=(conn, addr)).start() # add connection to array to send data through it later