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

# Global Variables
lock = threading.Lock()                     # lock for threads

# function that uses regex for command used for fixing and failing links
def check_command_letter_number(string, desired_command):
    pattern = r'({0})\(([A-Za-z])(\d+)\)'.format(desired_command)       # regex pattern for command
    match = re.search(pattern, string)                                  # search for pattern in string
    if match:                                                # if match is found
        command = match.group(1)                            # get command
        letter = match.group(2)                             # get letter
        number = match.group(3)                             # get number
        return command, letter, number                      # return command, letter, and number
    return None                                 # if no match is found return None

# function that uses regex for command used for extracting command and string
def extract_command_and_string(string, desired_command):
    pattern = r"({0})\((.*?)\)".format(desired_command)     # regex pattern for command
    match = re.search(pattern, string)                      # search for pattern in string
    if match:                                               # if match is found
        command = match.group(1)                            # get command
        extracted_string = match.group(2)                   # get string
        return command, extracted_string                    # return command and string
    return None                                 # if no match is found return None

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
    global ballotNum
    nodeBlockChainLogFileName = f"Node_{nodeID}_Blockchain_Log.txt"
    blogFile = f"Node_{nodeID}_Blog.txt"
        
    while True:
        userInput = input()    # wait for user input

        view = extract_command_and_string(userInput, "view")            # extract view command
        read = extract_command_and_string(userInput, "read")            # extract read command
        wait = extract_command_and_string(userInput, "wait")            # extract wait command
        post = extract_fields_from_command(userInput, "post")           # extract post command
        fixLink = check_command_letter_number(userInput, "fixLink")     # extract fixLink command
        comment = extract_fields_from_command(userInput, "comment")     # extract comment command
        failLink = check_command_letter_number(userInput, "failLink")   # extract failLink command

        if  userInput == "crash":                       # crash the program
            inBoundSocket.close()                       # close all sockets before exiting
            print("Crashing Program...", flush=True)
            stdout.flush()                              # flush console output buffer in case there are remaining prints
            _exit(0)                                    # exit program with status 0

        if failLink != None:                                                                                             # fail a link between desired nodes format: failLink(Nx)
            nodeToFail = failLink[-1]
            print("Failing connection from node: " + str(nodeID) + " to node: " + str(nodeToFail) + "...", flush=True)   # print message to console
            outBoundSockets[int(nodeToFail)].sendall(f"FAIL {nodeID}".encode())                                          # send fail message to other node
            del outBoundSockets[int(nodeToFail)]                                                                         # delete socket from outBoundSockets
            print("Connection from node: " + str(nodeID) + " to node: " + str(nodeToFail) + " failed\n", flush=True)     # print message to console

        if fixLink != None:                                                                                              # fix a link between desired nodes format: finxLink(Nx)
            nodeToFix = fixLink[-1]
            print("Fixing connection from node: " + str(nodeID) + " to node: " + str(nodeToFix) + "...", flush=True)     # print message to console
            addConns(int(nodeToFix))                                                                                     # add socket back to outBoundSockets
            outBoundSockets[int(nodeToFix)].sendall(f"FIX {nodeID}".encode())                                            # send fix message to other node
            print("Connection from node: " + str(nodeID) + " to node: " + str(nodeToFix) + " fixed\n", flush=True)       # print message to console

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

        if post != None:              # post a new post format: post(username, title, content)
            command = post[0]         # get command
            username = post[1]        # get username
            title = post[2]           # get title
            content = post[3]         # get content

            if leadID != nodeID and leadID != None:
                formatString = command + "(" + username + ", " + title + ", " + content + ")"                                                                                                                   # print message to console
                outBoundSockets[int(leadID)].sendall(bytes(f"FORWARD {nodeID} {str(blockchain.returnBlockLength())} {formatString}","utf-8"))                 # forward message

            if command == "post" and blockchain.isValidPost(title) == True:
                print("DUPLICATE TITLE", flush=True)
           
            elif leadID == nodeID:                                # pseudo leader
                print("Inserting post into queue...", flush=True) # print message to console
                
                queue.append(userInput)

                blockToAdd = Block(blockchain.getLatestBlock().hash, command, username, title, content)
                blockchain.appendBlock(blockToAdd)

                print("Sending Accept Message...", flush=True) 
                for node in outBoundSockets.values():                                                                                                           
                    formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
                    node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {str(ballotNum)} {formatString}".encode())      # send accept message to other nodes

            elif leadID == None:                                    # pseudo proposer
                print("Inserting post into queue...", flush=True) # print message to console
                print("Sending Prepare Message...", flush=True)                                                # print message to console
                ballotNum = ballotNum + 1
                print("Ballot Number: " + str(ballotNum), flush=True)                                          # print message to console
                for node in outBoundSockets.values():                                                          # iterate through outbound sockets
                    # FIX BALLOT NUM HERE IN PLACE OF STR(1)
                    formatString = str(command) + "(" + str(username) + ", " + str(title) + ", " + str(content) + ")"
                    node.sendall(f"PREPARE {nodeID} {str(ballotNum)} {blockchain.returnBlockLength()} {formatString}".encode())    # send prepare message to other nodes

        # if comment != None:                                                   # post a new comment format: comment(username, title, content)
        #     command = comment[0]
        #     username = comment[1]
        #     title = comment[2]
        #     content = comment[3]

        #     if leadID != nodeID and leadID != None:
        #         formatString = command + "(" + username + ", " + title + ", " + content + ")"                                                                                                                   # print message to console
        #         outBoundSockets[int(leadID)].sendall(bytes(f"FORWARD {nodeID} {str(blockchain.returnBlockLength())} {formatString}","utf-8"))                 # forward message

        #     if command == "comment" and blockchain.isValidPost(title) == False:
        #         print("CANNOT COMMENT", flush=True)
           
        #     elif leadID == nodeID:                                # pseudo leader
        #         print("Inserting post into queue...", flush=True) # print message to console

        #         queue.append(userInput)

        #         blockToAdd = Block(blockchain.getLatestBlock().hash, command, username, title, content)
        #         blockchain.appendBlock(blockToAdd)
                
        #         print("Sending Accept Message...", flush=True)                                                                                                                    # print message to console
        #         for node in outBoundSockets.values():
        #             formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
        #             node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {formatString}".encode())      # send accept message to other nodes

        #     elif leadID == None:                                    # pseudo proposer
        #         print("Inserting post into queue...", flush=True) # print message to console
        #         print("Sending Prepare Message...", flush=True)                                            # print message to console
        #         for node in outBoundSockets.values():                                                          # iterate through outbound sockets
        #             node.sendall(f"PREPARE {nodeID} {blockchain.returnBlockLength()} {userInput}".encode())    # send prepare message to other nodes

        if userInput == "blog":                         # if user input is blog
            if blockchain.returnBlockLength() == 1:     # if blockchain is empty
                print("BLOG EMPTY", flush=True)         # print 'empty' message to console
            
            else:                                       # if blockchain is not empty
                print("Printing blog...", flush=True)   # print 'printing' to console
                count = 0                               # init count for skipping genesis block
                titleOfPosts = []                       # init list of titles which contain the post Titles
                
                for block in blockchain.chain:          # iterate through blockchain
                    if count == 0:                      # skip genesis block
                        count = count + 1           
                        continue

                    if block.operation == "post" or block.operation == "comment":                 # if block operation is post or a comment
                        titleOfPosts.append(block.title)                                          # append block title to list of titles
    
                for title in titleOfPosts:                        # iterate through list of titles
                    print(str(title), flush=True)                 # print title to console

        if view != None:                                                                            # view post by username format: view(user)
            userContents = []                                                                       # init list of user contents
            desiredUser = view[-1]                                                                  # get username
            count = 0

            for block in blockchain.chain:                                                                                     # iterate through blockchain
                if count == 0:                                # skip genesis block
                        count = count + 1
                        continue
                
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

                blockToAdd = Block(blockchain.getLatestBlock().hash, str(splicedRow[1]),  str(splicedRow[2]), title, contents)  # create block
                blockchain.appendBlock(blockToAdd)                                                              # add block
                blockchainHistory = blockchain.getBlogChain()

            content = open(blogFile, 'r').readlines()
            for row in content:                                            # iterate through file
                row = row[:-1]                                             # ignore endlines
                operation, username, title, contents = extract_fields(row)
                splicedRow = row.split(" ")                                # split row by spaces
                blogApp.commitPost(splicedRow[0], splicedRow[1], str(title), str(contents))            # add post to blog

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
            print("waiting " + str(time) + " seconds")  # print waiting time to console
            sleep(int(time))                            # sleep for specified time from wait command

        if userInput == "leader":                           # if user input is leader
            print(str(leadID) + "   " + str(type(leadID)))  # print leader ID

        if userInput == "nodes":                            # if user input is nodes
            print(outBoundSockets.keys())                   # print all node IDs

def handle_msg(data, conn, addr):                      # simulates network delay then handles received message
    global leadID                       # global leader ID
    global acceptCount                  # global accept count
    global promiseCount                 # global promise count
    global ballotNum                    # global ballot number
    global acceptNum                    # global accept number

    lock.acquire()                                     # acquire lock

    nodeBlockChainLogFileName = f"Node_{nodeID}_Blockchain_Log.txt" # init blockchain log file name
    blogFile = f"Node_{nodeID}_Blog.txt"                            # init blog file name

    sleep(3)                                       # simulate network delay

    data = data.decode()                        # decode byte data into a string
    splitData = data.split(" ")                 # split data by spaces
    print("DATA: " + str(data), flush=True)     #print the data received

    if splitData[0] == "PREPARE":
        pattern = r'(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\((\w+)(?:\s*,\s*(.*?))?(?:\s*,\s*(.*?))?\)'
        match = re.match(pattern, str(data))
        if match:
            command = match.group(1)
            node_ID = int(match.group(2))
            blockchainLength = int(match.group(3))
            bal = int(match.group(4))
            operation = match.group(5)
            user = match.group(6)
            title = match.group(7)
            contents = match.group(8)
    
    if splitData[0] == "PROMISE":
        pattern = r'(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\((\w+)(?:\s*,\s*(.*?))?(?:\s*,\s*(.*?))?\)'
        match = re.match(pattern, str(data))
        if match:
            command = match.group(1)
            node_ID = int(match.group(2))
            blockchainLength = int(match.group(3))
            bal = int(match.group(4))
            acceptNum = int(match.group(5)) 
            operation = match.group(6)
            user = match.group(7)
            title = match.group(8)
            contents = match.group(9)
            
    if splitData[0] == "ACCEPT":
        pattern = r'(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\((\w+)(?:\s*,\s*(.*?))?(?:\s*,\s*(.*?))?\)'
        match = re.match(pattern, str(data))
        if match:
            command = match.group(1)
            node_ID = int(match.group(2))
            blockchainLength = int(match.group(3))
            bal = int(match.group(4))
            acceptNum = int(match.group(5)) 
            operation = match.group(6)
            user = match.group(7)
            title = match.group(8)
            contents = match.group(9)
    
    if splitData[0] == "ACCEPTED":
        pattern = r'(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\((\w+),\s*([\w\s]+),\s*([\w\s]+)\)'
        match = re.match(pattern, str(data))
        if match:
            command = match.group(1)
            node_ID = int(match.group(2))
            blockchainLength = int(match.group(3))
            bal = int(match.group(4))
            operation = match.group(5)
            user = match.group(6)
            title = match.group(7)
            contents = match.group(8)

    if splitData[0] == "DECIDE":
        pattern = r'(\w+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\w+)\((\w+),\s*([\w\s]+),\s*([\w\s]+)\)'
        match = re.match(pattern, str(data))
        if match:
            command = match.group(1)
            node_ID = int(match.group(2))
            blockchainLength = int(match.group(3))
            bal = int(match.group(4))
            operation = match.group(5)
            user = match.group(6)
            title = match.group(7)
            contents = match.group(8)

    if splitData[0] == "FORWARD":
        pattern = r'(\w+)\s+(\d+)\s+(\d+)\s+(\w+)\((\w+),\s*([\w\s]+),\s*([\w\s]+)\)'
        match = re.match(pattern, str(data))
        if match:
            command = match.group(1)
            node_ID = int(match.group(2))
            blockchainLength = int(match.group(3))
            operation = match.group(4)
            user = match.group(5)
            title = match.group(6)
            contents = match.group(7)

    try:

            if command == "PREPARE" and int(blockchainLength) >= blockchain.returnBlockLength():
                    if (bal > ballotNum) or (bal == ballotNum and node_ID > int(nodeID)):
                        ballotNum = bal
                        print(f"Received PREPARE from node {node_ID}...")
                        logOperation = operation+"(" + user +", " + title + ", " + contents + ")"
                        outBoundSockets[int(node_ID)].sendall(f"PROMISE {nodeID} {str(blockchain.returnBlockLength())} {bal} {acceptNum} {logOperation}".encode())
            
            if command == "PROMISE":
                print(f"Received PROMISE from node {node_ID}...")
                promiseCount += 1
                if promiseCount >= math.ceil((len(outBoundSockets) + 1)/2):
                    if operation != None:

                        promiseCount = 0
                        leadID = nodeID

                        logOperation = str(blockchainLength) + " (" + operation +", " + user + ", " + title + ")"
                        queue.append(logOperation)

                        blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)
                        blockToAdd.calcNonce()
                        
                        for node in outBoundSockets.values():
                            formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"
                            node.sendall(f"ACCEPT {nodeID} {str(blockchain.returnBlockLength())} {bal} {acceptNum} {formatString}".encode())

            if command == "ACCEPT" and int(blockchainLength) >= blockchain.returnBlockLength():
                print(f"Received ACCEPT from node {node_ID}...")
                if (bal > ballotNum) or (bal == ballotNum and node_ID > int(nodeID)):
                    acceptNum = bal
    
                leadID = int(node_ID)
                logOperation = operation+"(" + user +", " + title + ", " + contents + ")"

                outBoundSockets[int(node_ID)].sendall(f"ACCEPTED {nodeID} {str(blockchain.returnBlockLength())} {bal} {logOperation}".encode())

                with open(nodeBlockChainLogFileName, "a") as log:
                        log.write(f"TENTATIVE {logOperation}\n")

            if command == "ACCEPTED":
                sleep(0.5)
                print(f"Received ACCEPTED from node {node_ID}...")
                acceptCount = acceptCount + 1

                if acceptCount >= math.ceil((len(outBoundSockets) + 1)/2):
                    acceptCount = 0
                    blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)
                    blockchain.appendBlock(blockToAdd)

                    with open(nodeBlockChainLogFileName, "a") as log:
                        log.write(f"CONFIRMED: {blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n")

                    blogApp.commitPost(operation, user, title, contents)

                    with open(blogFile, "a") as log:
                        log.write(f"{blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n")

                    queue.pop(0)

                    if operation == "post":                             #if the operation is post
                        print(f"NEWPOST: <{title}> from <{user}>")      #print the new post
        
                    if operation == "comment":                          #if the operation is comment
                        print(f"NEW COMMENT: <{title}> from <{user}>")  #print the new comment

                    for node in outBoundSockets.values():               #for each node in the outbound sockets
                        formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"    
                        # FIX bal num
                        node.sendall(f"DECIDE {nodeID} {str(blockchain.returnBlockLength())} {str(1)} {formatString}".encode())

            if command == "DECIDE":                                                                     #if the command is decide
                print(f"Received DECIDE from node {node_ID}...")                                        #print the received decide
                blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)  #create a new block
                blockchain.appendBlock(blockToAdd)                                                      #append the block to the blockchain
                content = open(nodeBlockChainLogFileName, 'r').readlines()                              #read the contents of the log file
                content[-1] = f"CONFIRMED: {blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n"
                out = open(nodeBlockChainLogFileName, 'w')
                out.writelines(content)
                out.close()
                blogApp.commitPost(operation, user, title, contents)
                with open(blogFile, "a") as log:
                        log.write(f"{blockToAdd.operation} {blockToAdd.user} title: {blockToAdd.title} contents: {blockToAdd.contents}\n")

                if operation == "post":                                 # if the operation is post
                    print(f"NEW POST: {title} from {user}.")            # print the new post

                if operation == "comment":                              # if the operation is comment
                    print(f"NEW COMMENT: on {title} from {user}.")      # print the new comment

            if command == "FORWARD":                                    # if FORWARD command received
                print(f"Received FORWARD from node: {node_ID}...")      # print that the forward was received
                if leadID == nodeID:                                    # if the leadID is the same as the nodeID
                    logOperation = operation + " " + user + " " + title + " " + contents                    # create the log operation
                    queue.append(logOperation)                                                              # append the log operation to the queue
                    blockToAdd = Block(blockchain.getLatestBlock().hash, operation, user, title, contents)  # create the block to add
                    blockToAdd.calcNonce()                                                                  # calculate the nonce for the block
                    for node in outBoundSockets.values():                                                   # for each node in the outbound sockets
                        formatString = str(blockToAdd.operation) + "(" + str(blockToAdd.user) + ", " + str(blockToAdd.title) + ", " + str(blockToAdd.contents) + ")"    # create the format string
                        node.sendall(f"ACCEPT {nodeID} {blockchain.returnBlockLength()} {str(0)} {str(0)} {formatString}".encode())                                                       # send the accept to the node
                else:
                    outBoundSockets[leadID].sendall(f"FORWARD {nodeID} {str(blockchain.returnBlockLength())} {logOperation}".encode())                                  # send the forward to the leadID

            if command == "RECONNECT":                          # if RECONNECT command received, add connection to dictionary
                print(f"Now Reconnecting to node: {node_ID}")   # print reconnecting message
                addConns(int(node_ID))                          # add connection to dictionary

            if command == "FIX":                                                            # if FIX command received, add connection to dictionary
                addConns(int(node_ID))                                                      # add connection to dictionary
                print(f"Connection to node: {node_ID} has now been fixed.", flush=True)     # print confirmation of fix message

            if command == "FAIL":                                                   # if FAIL command received, delete connection from dictionary
                del outBoundSockets[int(node_ID)]                                   # delete connection from dictionary
                print(f"Connection to node: {node_ID} has failed.", flush=True)     # print failure message

    except Exception:            # if exception raised, print exception and traceback
        traceback.print_exc()    # print traceback
    
    lock.release()               # release lock

def respond(conn, addr):              # handle a new connection by waiting to receive from connection 

    while True:                       # infinite loop to keep waiting to receive new data from this client
        try:
            data = conn.recv(1024)
        except:
            conn.close()                                                        # if exception raised in receiving, close connection and
            delConns()                                                          # delete connection from dictionary
            print(f"Exception raised in receiving from {addr[1]}.", flush=True) # if exception raised in receiving, close connection and
            break
        if not data:                                                            # if client's socket closed, it will signal closing without any data
            conn.close()                                                        # close own socket to client since other end is closed
            print(f"Connection has been closed from {addr[1]}.", flush=True)    # print that connection has been closed
            break

        threading.Thread(target=handle_msg, args=(data,conn, addr)).start()     # new thread to handle message so simulated network delay and message handling don't block receive

def getConns():                # function to get connections to all nodes
    count = 0                  # count of connections
    while True:
        try:
            conn, addr = inBoundSocket.accept()                 # accept a new connection
        except:
            print("Exception in accept.", flush= True)          # if exception in accept, break out of loop
            break
        print("Connected to the inbound client", flush=True)    # print that a new connection has been made
        count = count + 1                                       # increment count of connections

        if count == 2: #CHANGE TO 4 b4 demo
            print("All nodes have been connected...\n", flush=True)  # print that all nodes have been connected
        threading.Thread(target=respond, args=(conn,addr)).start()   # new thread to handle connection so that multiple connections can be handled at once

def delConns():                                 # function to delete a connection to a node
    failedConns = []                            # list of failed connections
    for id, node in outBoundSockets.items():    # iterate through all connections
        try:
            node.sendall("ping".encode())       # send ping to check if connection is still alive
        except:
            failedConns.append(id)              # if ping fails, add connection to list of failed connections
    for id in failedConns:                      # iterate through failed connections
        del outBoundSockets[id]                 # delete connection from dictionary

def addConns(nodeID):                                                       # function to add a new connection to a node
    if id not in outBoundSockets:                                           # if connection doesn't already exist
        try:
            out_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    # create new socket
            out_sock.connect((IP, 9000 + nodeID))                           # connect to node
            outBoundSockets[nodeID] = out_sock                              # add socket to dictionary
            print(f"Connected to outbound node: {nodeID}", flush=True)      # print confirmation of connection
        except:
            print(f"Failed to connect to outbound client node: {nodeID}", flush=True)   # print failure to connect

if __name__ == "__main__":
    nodeID = str(sys.argv[1])                   # get node ID from command line
    nodeID = nodeID.replace("N", "")            # remove N from node ID

    queue = []                                  # queue to store messages
    IP = socket.gethostname()                   # get IP address
    portNum = 9000 + int(nodeID)                # set port number

    blogApp = Blog()                            #initalize blog
    outBoundSockets = {}                        # dictionary of outbound sockets
    blockchain = Blockchain()                   #initalize blockchain

    # PAXOS VARIABLES
    leadID = None                               # leader ID
    acceptCount = 0                             # accept count
    promiseCount = 0                            # promise count

    global ballotNum
    global acceptNum
    ballotNum = 0                               # ballot number
    acceptNum = 0                               # accept number

    inBoundSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)             # create a socket object, SOCK_STREAM specifies a TCP socket
    inBoundSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)           # when REUSEADDR is not set
    inBoundSocket.bind((IP, portNum))                                             # bind socket to address
    inBoundSocket.listen()                                                        # start listening for connections to the address
    threading.Thread(target=getConns).start()                                     # start thread to listen for new connections

    sleep(8)                                                                      # time to initiate connections between every node
    
    # if int(nodeID) == 1:
    #     addConns(2)
    #     addConns(3)
 
    # if int(nodeID) == 2:
    #     addConns(1)
    #     addConns(3)

    # if int(nodeID) == 3:
    #     addConns(1)
    #     addConns(2)

    if int(nodeID) == 1:
        addConns(2)
        addConns(3)
        addConns(4)
        addConns(5)

    if int(nodeID) == 2:
        addConns(1)
        addConns(3)
        addConns(4)
        addConns(5)

    if int(nodeID) == 3:
        addConns(1)
        addConns(2)
        addConns(4)
        addConns(5)
    
    if int(nodeID) == 4:
        addConns(1)
        addConns(2)
        addConns(3)
        addConns(5)
    
    if int(nodeID) == 5:
        addConns(1)
        addConns(2)
        addConns(3)
        addConns(4)

    threading.Thread(target=get_userInput).start() 
    