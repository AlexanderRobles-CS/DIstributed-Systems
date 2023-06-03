
import hashlib

# init block
class Block:
    def __init__(self, sender, receiver, amount, prevHash, lamportClock):
        self.lamportClock = lamportClock    # lamport clock
        self.prevHash = prevHash            # hash of previous block
        self.sender = sender                # sender of transaction
        self.receiver = receiver            # receiver of transaction
        self.amount = amount                # amount of transaction
        self.nonce = 0                      # nonce value
        self.hash = self.calcHash()         # hash of current block
    
    # calculate hash of new block
    def calcHash(self):
        sha256 = hashlib.sha256()                           # sha256 hash function

        sha256.update(str(self.prevHash).encode('utf-8') +
                   str(self.sender).encode('utf-8') +
                   str(self.receiver).encode('utf-8') +
                   "$".encode('utf-8') +
                   str(self.amount).encode('utf-8') +
                   str(self.nonce).encode('utf-8'))         # hash of previous block, sender, receiver, amount, and nonce all concatenated together
        return sha256.hexdigest()                           # return hash in hexidecimal

    # mining nonce function
    def calcNonce(self):

        while int(self.hash[0], 16) >= 4:   # look for 2 leading 0s in hex, if not found, increment nonce and recalculate hash
            self.nonce += 1                 # increment nonce
            self.hash = self.calcHash()     # recalculate hash

# init blockchain
class Blockchain:
    def __init__(self):
        self.chain = [self.createGenesis()]             # create genesis block of blockchain
        self.chain[0].hash = self.chain[0].prevHash     # set hash of genesis block to hash of previous block

    # create genesis block
    def createGenesis(self):                            
        genisisBlockHash = "0" * 64                     # hash of genesis block is 64 0s
        return Block("Genesis Block", "Genesis Block", 0, genisisBlockHash, "<0,0>")    # return genesis block for blockchain

    def getLatestBlock(self): 
    # get latest block on blockchain
    # used for getting previous block data memebers
        return self.chain[-1]

    # append new block to blockchain
    def appendBlock(self, newBlock, sender, receiver, amount):
        newBlock.sender = sender                            # set sender for new block
        newBlock.receiver = receiver                        # set receiver for new block
        newBlock.amount = amount                            # set amount for new block
        newBlock.prevHash = self.getLatestBlock().hash      # set previous hash of new block to hash of latest block
        newBlock.calcNonce()                                # calculate nonce for new block
        newBlock.lamportClock = newBlock.lamportClock       # set lamport clock for new block
        
        self.chain.append(newBlock)                         # append new block to blockchain
    
    # calculate balance of a given user
    def getBalance(self, sender):
        balance = 10                                     # set initial balance to 10
        for block in self.chain:                         # iterate through blockchain
            if block.sender == sender:                   # if sender is the sender of the transaction
                balance = balance - int(block.amount)    # subtract amount from balance
            elif block.receiver == sender:               # if sender is the receiver of the transaction
                balance =  balance + int(block.amount)   # add amount to balance
        return balance