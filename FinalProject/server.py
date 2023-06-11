import re
import sys
import math
import socket
import threading
import traceback
import blockchain

from os import _exit
from sys import stdout
from time import sleep
from blogApp import Blog
from blockchain import Blockchain, Block

# function that uses regex for command used for fixing and failing links
def check_command_letter_number(string, desired_command):
    pattern = r'({0})\(([A-Za-z])(\d+)\)'.format(desired_command)
    match = re.search(pattern, string)
    if match:
        command = match.group(1)
        letter = match.group(2)
        number = match.group(3)
        return command, letter, number
    return None

# function that uses regex for command used for extracting command and string
def extract_command_and_string(string, desired_command):
    pattern = r"({0})\((.*?)\)".format(desired_command)
    match = re.search(pattern, string)
    if match:
        command = match.group(1)
        extracted_string = match.group(2)
        return command, extracted_string
    return None

# function used for post and comment commands
def extract_fields_from_command(string, desired_command):
    pattern = r"({0})\((.*?), (.*?), (.*?)\)".format(desired_command)
    match = re.search(pattern, string)
    if match:
        command = match.group(1)
        username = match.group(2)
        title = match.group(3)
        content = match.group(4)
        return command, username, title, content
    return None

def extract_fields(input_string):
    # Extracting the post field
    post_match = re.search(r"\bpost\s+(\w+)", input_string)
    post = post_match.group(1) if post_match else None

    # Extracting the username
    username_match = re.search(r"\bpost\s+(\w+)", input_string)
    username = username_match.group(1) if username_match else None

    # Extracting the title
    title_match = re.search(r"title:\s*(.*?)\s+contents:", input_string)
    title = title_match.group(1) if title_match else None

    # Extracting the contents
    contents_match = re.search(r"contents:\s*(.*)$", input_string)
    contents = contents_match.group(1) if contents_match else None

    return post, username, title, contents

def get_userInput():
    global leadID
    nodeBlockChainLogFileName = f"Node_{nodeID}_Blockchain_Log.txt"
    blogFile = f"Node_{nodeID}_Blog.txt"
        
    while True:
        userInput = input()                     # wait for user input

        failLink = check_command_letter_number(userInput, "failLink")
        fixLink = check_command_letter_number(userInput, "fixLink")
        view = extract_command_and_string(userInput, "view")
        read = extract_command_and_string(userInput, "read")
        wait = extract_command_and_string(userInput, "wait")
        comment = extract_fields_from_command(userInput, "comment")
        post = extract_fields_from_command(userInput, "post")

        if  userInput == "crash":                       # crash the program
            inBoundSocket.close()                       # close all sockets before exiting
            print("Crashing Program...", flush=True)
            stdout.flush()                              # flush console output buffer in case there are remaining prints
            _exit(0)                                    # exit program with status 0

        if failLink != None:                                                                                                        # fail a link between desired nodes format: failLink(Nx)
            nodeToFail = failLink[-1]
            print("Failing connection from node: " + str(nodeID) + " to node: " + str(nodeToFail) + "...", flush=True)              # print message to console
            outBoundSockets[int(nodeToFail)].sendall(f"FAIL {nodeID}".encode())                                                     # send fail message to other node
            del outBoundSockets[int(nodeToFail)]                                                                                    # delete socket from outBoundSockets
            print("Connection from node: " + str(nodeID) + " to node: " + str(nodeToFail) + " failed\n", flush=True)                # print message to console

        if fixLink != None:                                                                                                         # fix a link between desired nodes format: finxLink(Nx)
            nodeToFix = fixLink[-1]
            print("Fixing connection from node: " + str(nodeID) + " to node: " + str(nodeToFix) + "...", flush=True)                # print message to console
            addConns(int(nodeToFix))                                                                                                # add socket back to outBoundSockets
            outBoundSockets[int(nodeToFix)].sendall(f"FIX {nodeID}".encode())                                                       # send fix message to other node
            print("Connection from node: " + str(nodeID) + " to node: " + str(nodeToFix) + " fixed\n", flush=True)                  # print message to console

        if userInput == "blockchain":                            # iterate through blockchain to append to history array
            if(blockchain.returnBlockLength() == 1):             # if blockchain is empty
                print("Blockchain is empty\n", flush=True)
            else:
                print("Printing blockchain...", flush=True)          # print message to console
                blockchainHistory = blockchain.getBlogChain()        # get blockchain history

                for block in blockchainHistory[1:]:                  # iterate through blockchain history
                    print(block, flush=True)                         # print each block to console

        if userInput == "queue":                              # print queue
            if(len(queue) == 0):                              # if queue is empty
                print("Queue is empty\n", flush=True)         # print message to console
            else:                                             # if queue is not empty
                print("Queue:", flush=True)
                print(queue, flush=True)                      # print queue to console
                print("\n", flush=True)

        if post != None:                                                   # post a new post format: post(username, title, content)
            command = post[0]
            username = post[1]
            title = post[2]
            content = post[3]

            if command == "post" and blockchain.isValidPost(title) == True:
                print("DUPLICATE TITLE", flush=True)
           
            elif leadID == nodeID:                                # pseudo leader
                
                queue.append(userInput)

                blockToAdd = Block(blockchain.getLatestBlock().hash, command, username, title, content)
                blockchain.appendBlock(blockToAdd)

                for node in outBoundSockets.values():
                    print("Sending Accept Message...", flush=True)                                                                                                                    # print message to console
                    formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
                    node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {formatString}".encode())      # send accept message to other nodes

            elif leadID == None:                                    # pseudo proposer
                
                for node in outBoundSockets.values():                                                          # iterate through outbound sockets
                    print("Sending Prepare Message...", flush=True)                                            # print message to console
                    node.sendall(f"PREPARE {nodeID} {blockchain.returnBlockLength()} {userInput}".encode())    # send prepare message to other nodes
        
            else:                                                  # pseudo acceptor
                outBoundSockets[int(leadID)].sendall(f"FORWARD {nodeID} {userInput}".encode())                 # forward message

        if comment != None:                                                   # post a new comment format: comment(username, title, content)
            command = comment[0]
            username = comment[1]
            title = comment[2]
            content = comment[3]

            if command == "comment" and blockchain.isValidPost(title) == False:
                print("CANNOT COMMENT", flush=True)
           
            elif leadID == nodeID:                                # pseudo leader
                
                queue.append(userInput)

                blockToAdd = Block(blockchain.getLatestBlock().hash, command, username, title, content)
                blockchain.appendBlock(blockToAdd)

                for node in outBoundSockets.values():
                    print("Sending Accept Message...", flush=True)                                                                                                                    # print message to console
                    formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
                    node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {formatString}".encode())      # send accept message to other nodes

            elif leadID == None:                                    # pseudo proposer
                
                for node in outBoundSockets.values():                                                          # iterate through outbound sockets
                    print("Sending Prepare Message...", flush=True)                                            # print message to console
                    node.sendall(f"PREPARE {nodeID} {blockchain.returnBlockLength()} {userInput}".encode())    # send prepare message to other nodes
        
            else:                                                  # pseudo acceptor
                outBoundSockets[int(leadID)].sendall(f"FORWARD {nodeID} {userInput}".encode())                 # forward message

        if userInput == "blog":
            if blockchain.returnBlockLength() == 1:
                print("BLOG EMPTY", flush=True)
            
            else:
                print("Printing blog...", flush=True)
                count = 0                                         # init count for skipping genesis block
                titleOfPosts = []                                 # init list of titles which contain the post Titles
                
                for block in blockchain.chain:                    # iterate through blockchain
                    if count == 0:                                # skip genesis block
                        count = count + 1
                        continue

                    if block.operation == "post" or block.operation == "comment":                 # if block operation is post or a comment
                        titleOfPosts.append(block.title)                                          # append block title to list of titles
    
                for title in titleOfPosts:                        # iterate through list of titles
                    print(str(title), flush=True)                 # print title to console

        if view != None:                                                                            # view post by username format: view(user)
            userContents = []                                                                       # init list of user contents
            desiredUser = view[-1]                                                                  # get username

            for block in blockchain.chain:                                                                                     # iterate through blockchain
                if desiredUser == block.user:                                                                                  # if block username is username
                    userContents.append(("Title: " + str(block.title), "Contents: " + str(block.contents)))                    # append block to list of user contents

            if len(userContents) == 0:
                print("NO POST", flush=True)
            else:
                print("Viewing posts by " + desiredUser + "...", flush=True)                                                   # print message to console
                for content in userContents:
                    print(str(content[0]) + " " + str(content[1]), flush=True)

        if read != None:                                                     # read post by title format read(title)
            titleContents = []                                               # init list of title contents
            desiredTitle = read[-1]                                          # get title

            for block in blockchain.chain:                                   # iterate through blockchain
                if desiredTitle == block.title:                              # if block title is title
                    titleContents.append((block.user, block.contents))       # append block to list of title contents

            if len(titleContents) == 0:                                      # if title not found
                print("POST NOT FOUND", flush=True)                          # print message to console
            else:
                for blogPost in titleContents:                                       # iterate through list of title contents
                    print(str(blogPost[0]) + ": " + str(blogPost[1]), flush=True)    # print post to console

        if userInput == "load":
            content = open(nodeBlockChainLogFileName, 'r').readlines()

            for row in content:                                             # iterate through file
                row = row[:-1]                                             # ignore endlines
                splicedRow = row.split(" ")                                # split row by spaces
                operation, username, title, contents = extract_fields(row)

                blockToAdd = Block(blockchain.getLatestBlock().hash, str(splicedRow[1]),  str(splicedRow[2]), title, contents)  # create block                                                                                     # calculate block nonce
                blockchain.appendBlock(blockToAdd)                                                              # add block\
                blockchainHistory = blockchain.getBlogChain()
                print(blockchainHistory)

            content = open(blogFile, 'r').readlines()
            for row in content:                                            # iterate through file
                row = row[:-1]                                             # ignore endlines
                operation, username, title, contents = extract_fields(row)
                splicedRow = row.split(" ")                                # split row by spaces
                blogApp.add_post(splicedRow[0], splicedRow[1], str(title), str(contents))            # add post to blog

        if userInput == "exit":
            inBoundSocket.close()                          # close all sockets before exiting
            print("Exiting Program...\n", flush=True)
            stdout.flush()                                 # flush console output buffer in case there are remaining prints
            _exit(0)                                       # exit program with status 0

        if userInput == "reconnect":                                # reconnect to all nodes
            for sock in outBoundSockets.values():                   # send reconnect message to all nodes
                sock.sendall(f"RECONNECT {nodeID}".encode())        

        if wait != None:                 # wait function used in autograder
            time = wait[-1]
            print("waiting " + str(time) + " seconds")
            sleep(int(time))

def handle_msg(data, conn, addr):                      # simulates network delay then handles received message
    global leadID
    global acceptCount
    global promiseCount

    nodeBlockChainLogFileName = f"Node_{nodeID}_Blockchain_Log.txt"
    blogFile = f"Node_{nodeID}_Blog.txt"

    sleep(3)

    data = data.decode()                        # decode byte data into a string
    pattern = r"^(\S+)\s+(\d+)\s+(\d+)\s+(\S+)\(([^(),]+),\s*([^(),]+(?:\s+[^(),]+)*),\s*([^()]+(?:\s+[^(),]+)*)\)$"    # regex pattern for matching messages
    match = re.match(pattern, str(data))
    if match:
        command = match.group(1)
        node_ID = match.group(2)
        blockchainLength = match.group(3)
        operation = match.group(4)
        user = match.group(5)
        title = match.group(6)
        contents = match.group(7)

    try:

        if match:
            command = match.group(1)
            node_ID = match.group(2)
            blockchainLength = match.group(3)
            operation = match.group(4)
            user = match.group(5)
            title = match.group(6)
            contents = match.group(7)

            if command == "PREPARE" and int(blockchainLength) >= blockchain.returnBlockLength():
                    print(f"Received PREPARE from node: {node_ID}...")

                    logOperation = operation+"(" + user +", " + title + ", " + contents + ")"
                    outBoundSockets[int(node_ID)].sendall(f"PROMISE {nodeID} {str(blockchain.returnBlockLength())} {logOperation}".encode())
            
            if command == "PROMISE":
                print(f"Received PROMISE from node: {node_ID}...")
                promiseCount += 1
                if promiseCount >= math.ceil((len(outBoundSockets) + 1)/2):
                    promiseCount = 0
                    leadID = nodeID

                    logOperation = blockchainLength+"(" + operation +", " + user + ", " + title + ")"
                    queue.append(logOperation)

                    blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)
                    blockToAdd.calcNonce()

                    for node in outBoundSockets.values():
                        formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
                        node.sendall(f"ACCEPT {nodeID} {str(blockchain.returnBlockLength())} {formatString}".encode())

            if command == "ACCEPT" and int(blockchainLength) >= blockchain.returnBlockLength():
                print(f"Received ACCEPT from node: {node_ID}...")

                leadID = int(node_ID)
                logOperation = operation+"(" + user +", " + title + ", " + contents + ")"

                outBoundSockets[int(node_ID)].sendall(f"ACCEPTED {nodeID} {str(blockchain.returnBlockLength())} {logOperation}".encode())

                with open(nodeBlockChainLogFileName, "a") as log:
                        log.write(f"TENTATIVE {logOperation}\n")

            if command == "ACCEPTED":
                sleep(0.5)
                print(f"Received ACCEPTED from node: {node_ID}...")
                acceptCount = acceptCount + 1

                if acceptCount >= math.ceil((len(outBoundSockets) + 1)/2):
                    acceptCount = 0
                    blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)
                    blockchain.appendBlock(blockToAdd)

                    with open(nodeBlockChainLogFileName, "a") as log:
                        log.write(f"CONFIRMED: {blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n")

                    blogApp.add_post(operation, user, title, contents)

                    with open(blogFile, "a") as log:
                        log.write(f"{blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n")

                    queue.pop(0)

                    if operation == "post":
                        print(f"NEWPOST: <{title}> from <{user}>")
        
                    if operation == "comment":
                        print(f"NEW COMMENT: <{title}> from <{user}>")

                    for node in outBoundSockets.values():
                        formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
                        node.sendall(f"DECIDE {nodeID} {str(blockchain.returnBlockLength())} {formatString}".encode())

            if command == "DECIDE":
                print(f"Received DECIDE from node: {node_ID}...")
                blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)
                blockchain.appendBlock(blockToAdd)
                content = open(nodeBlockChainLogFileName, 'r').readlines()
                content[-1] = f"CONFIRMED: {blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n"
                out = open(nodeBlockChainLogFileName, 'w')
                out.writelines(content)
                out.close()
                blogApp.add_post(operation, user, title, contents)
                with open(blogFile, "a") as log:
                        log.write(f"{blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n")

                if operation == "post":
                    print(f"NEW POST: {title} from {user}.")

                if operation == "comment":
                    print(f"NEW COMMENT: on {title} from {user}.")

            if command == "FORWARD":
                print(f"Received FORWARD from node: {node_ID}...")
                if leadID == nodeID:
                    logOperation = operation + " " + user + " " + title + " " + contents
                    queue.append(logOperation)
                    blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)
                    blockToAdd.calcNonce()
                    for node in outBoundSockets.values():
                        formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
                        node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {formatString}".encode())
                else:
                    outBoundSockets[leadID].sendall(f"FORWARD {nodeID} {str(blockchain.returnBlockLength())} {logOperation}".encode())

            if command == "RECONNECT":
                print(f"Now Reconnecting to node: {node_ID}")
                addConns(int(node_ID))

            if command == "FIX":
                addConns(int(node_ID))
                print(f"Connection to node: {node_ID} has now been fixed.", flush=True)

            if command == "FAIL":
                del outBoundSockets[int(node_ID)]
                print(f"Connection to node: {node_ID} has failed.", flush=True)

    except Exception:
        traceback.print_exc()

def respond(conn, addr):                            # handle a new connection by waiting to receive from connection 

    while True:                                     # infinite loop to keep waiting to receive new data from this client
        try:
            data = conn.recv(1024)
        except:
            conn.close()
            delConns()
            print(f"Exception raised in receiving from {addr[1]}.", flush=True)
            break
        if not data:                                                                 # if client's socket closed, it will signal closing without any data
            conn.close()                                                             # close own socket to client since other end is closed
            print(f"Connection has been closed from {addr[1]}.", flush=True)
            break

        threading.Thread(target=handle_msg, args=(data,conn, addr)).start()           # new thread to handle message so simulated network delay and message handling don't block receive

def getConns():
    count = 0
    while True:
        try:
            conn, addr = inBoundSocket.accept()
        except:
            print("Exception in accept.", flush= True)
            break
        print("Connected to the inbound client", flush=True)
        count = count + 1

        if count == 2: #CHANGE TO 4 b4 demo
            print("All nodes have been connected...\n", flush=True)
        threading.Thread(target=respond, args=(conn,addr)).start()

def delConns():
    failedConns = []
    for id, node in outBoundSockets.items():
        try:
            node.sendall("ping".encode())
        except:
            failedConns.append(id)
    for id in failedConns:
        del outBoundSockets[id]

def addConns(nodeID):
    if id not in outBoundSockets:
        try:
            out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            out_sock.connect((IP, 9000 + nodeID))
            outBoundSockets[nodeID] = out_sock
            print(f"Connected to outbound node: {nodeID}", flush=True)
        except:
            print(f"Failed to connect to outbound client node: {nodeID}", flush=True)

if __name__ == "__main__":
    nodeID = str(sys.argv[1])                   # get node ID from command line
    nodeID = nodeID.replace("N", "")            # remove N from node ID

    portNum = 9000 + int(nodeID)                # set port number
    queue = []                                  # queue to store messages
    IP = socket.gethostname()                   # get IP address

    blogApp = Blog()                            #initalize blog
    blockchain = Blockchain()                   #initalize blockchain
    outBoundSockets = {}                        # dictionary of outbound sockets

    # PAXOS VARIABLES
    leadID = None                               # leader ID
    promiseCount = 0                            # promise count
    acceptCount = 0                             # accept count

    inBoundSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # create a socket object, SOCK_STREAM specifies a TCP socket
    inBoundSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)           # when REUSEADDR is not set
    inBoundSocket.bind((IP, portNum))                                             # bind socket to address
    inBoundSocket.listen()                                                        # start listening for connections to the address
    threading.Thread(target=getConns).start()                                     # start thread to listen for new connections

    sleep(8)                                                                      # time to initiate connections between every node
    
    if int(nodeID) == 1:
        addConns(2)
        addConns(3)
 
    if int(nodeID) == 2:
        addConns(1)
        addConns(3)

    if int(nodeID) == 3:
        addConns(1)
        addConns(2)


    # if nodeID == 1:       CHANGE to all 5 servers
        # addConns(2)
        # addConns(3)
        # addConns(4)
        # addConns(5)

    # if nodeID == 2:
        # addConns(1)
        # addConns(3)
        # addConns(4)
        # addConns(5)

    # if idNum == 3:
        # addConns(1)
        # addConns(2)
        # addConns(4)
        # addConns(5)

    
    # if nodeID == 4:
        # addConns(1)
        # addConns(2)
        # addConns(3)
        # addConns(5)
    
    # if nodeID == 5:
        # addConns(1)
        # addConns(2)
        # addConns(3)
        # addConns(4)

    threading.Thread(target=get_userInput).start() 
    