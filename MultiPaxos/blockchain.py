
import hashlib

# init block
class Block:
    def __init__(self, prevHash, operation, user, title, contents):
        self.prevHash = prevHash            # hash of previous block
        self.user = user                    # user of block
        self.title = title                  # title of block
        self.contents = contents            # contents of block
        self.operation = operation          # operation of block
        self.nonce = 0                      # nonce value
        self.hash = self.calcHash()         # hash of current block
    
    # calculate hash of new block
    def calcHash(self):
        sha256 = hashlib.sha256()                           # sha256 hash function

        sha256.update(str(self.prevHash).encode('utf-8') +
                   str(self.operation).encode('utf-8') +
                   str(self.user).encode('utf-8') +
                   str(self.title).encode('utf-8') +
                   str(self.contents).encode('utf-8') +
                   str(self.nonce).encode('utf-8'))         # hash of previous block, operation, user, title, contents, and nonce
        return sha256.hexdigest()                           # return hash in hexidecimal

    # mining nonce function
    def calcNonce(self):

        while int(self.hash[0], 16) >= 3:   # look for 3 leading 0s
            self.nonce += 1                 # idncrement nonce
            self.hash = self.calcHash()     # recalculate hash

# init blockchain
class Blockchain:
    def __init__(self):
        self.chain = [self.createGenesis()]             # create genesis block of blockchain
        self.chain[0].hash = self.chain[0].prevHash     # set hash of genesis block to hash of previous block

    # create genesis block
    def createGenesis(self):                            
        genisisBlockHash = "0" * 64                     # hash of genesis block is 64 0s
        return Block(genisisBlockHash, "genesisOp", "genesisUser", "genesisTitle", "genesisContent")    # return genesis block for blockchain

    def getLatestBlock(self): 
    # get latest block on blockchain
    # used for getting previous block data memebers
        return self.chain[-1]

    def appendBlock(self, newBlock):                        # append new block to blockchain
        newBlock.calcNonce()                                # calculate nonce for new block
        self.chain.append(newBlock)                         # append new block to blockchain

    def isValidPost(self, title):
        for block in self.chain:                                          # iterate through blockchain
            if block.title == title and block.operation == "post":        # if block title is title
                return True                                              # return false
        return False                                                       # return true
    
    def getBlogChain(self):
        blog = []                                                                     # init list of posts
        for block in self.chain:                                                      # iterate through blockchain
            blog.append((block.hash ,block.nonce, block.operation, block.user, block.title, block.contents))   # append block to list of posts
        return blog
    
    def getUserPosts(self, user):
        userPosts = []                                                            # init list of posts from user
        for block in self.chain:                                                  # iterate through blockchain
            if block.user == user:                                                # if block user is user
                userPosts.append((block.title, block.contents))                   # append block to list of posts from user
        return userPosts                                                          # return list of posts from user
    
    def getPostComments(self, title):
        postComments = []                                                         # init list of comments on post
        for block in self.chain:                                                  # iterate through blockchain
            if block.operation == "post" and block.title == title:                # if block title is title and block operation is comment
                postComments.append((block.title, block.user, block.contents))    # append block to list of comments on post

        for block in self.chain:                                                  # iterate through blockchain
            if  block.op == "comment" and block.title == title:                   # if block title is title and block operation is comment
                postComments.append((block.user, block.contents))              # append block to list of comments on post
        return postComments                                                       # return list of comments on post
    
    def returnBlockLength(self):
        return len(self.chain)                                                    # return length of blockchain