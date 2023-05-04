
import hashlib

# init block
class Block:
    def __init__(self, sender, receiver, amount, prevHash, lamportClock):
        self.lamportClock = lamportClock
        self.prevHash = prevHash
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.nonce = 0
        self.hash = self.calculateHash()
    
    # calculate hash of new block
    def calculateHash(self):
        sha256 = hashlib.sha256()

        sha256.update(str(self.prevHash).encode('utf-8') +
                   str(self.sender).encode('utf-8') +
                   str(self.receiver).encode('utf-8') +
                   "$".encode('utf-8') +
                   str(self.amount).encode('utf-8') +
                   str(self.nonce).encode('utf-8'))
        return sha256.hexdigest()

    # mining nonce function
    def calcNonce(self):

        # linear search for nonce with correch hash
        # check if the hash in binary starts with the correct number of 0s
        # if not, increment nonce and recalculate hash
        while int(self.hash[0], 16) >= 4:
            self.nonce += 1
            self.hash = self.calculateHash()

# init blockchain
class Blockchain:
    def __init__(self):
        self.chain = [self.createGenesis()]
        self.chain[0].hash = self.chain[0].prevHash

    # create genesis block
    def createGenesis(self):
        genisisBlockHash = "0" * 64
        return Block("Genesis Block", "Genesis Block", 0, genisisBlockHash, "<0,0>")

    # get latest block on blockchain
    # used for getting previous block data memebers
    def getLatestBlock(self):
        return self.chain[-1]

    # append new block to blockchain
    def appendBlock(self, newBlock, sender, receiver, amount):
        newBlock.sender = sender
        newBlock.receiver = receiver
        newBlock.amount = amount
        newBlock.prevHash = self.getLatestBlock().hash
        newBlock.nonce = newBlock.calcNonce()
        newBlock.lamportClock = newBlock.lamportClock
        
        self.chain.append(newBlock)
    
    # calculate balance of a given user
    # iteratet through the blockchain 
    # add or subtract based upon if a user is the sender or the receiver
    def getBalance(self, sender):
        balance = 10
        
        for block in self.chain:
            if block.sender == sender:
                balance = balance - int(block.amount)

            elif block.receiver == sender:
                balance =  balance + int(block.amount)

        return balance