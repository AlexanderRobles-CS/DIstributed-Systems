class Blog:
    def __init__(self):                         # container for blog posts
        self.blogBin = {}                       # dictionary of blogs

    def commitPost(self, operation, user, title, contents):        # add post to blog
        if user not in self.blogBin:                        # if user doesn't have a blog yet
            self.blogBin[user] = []                         # create one

        self.blogBin[user].append((operation, title, contents))   # add post to blog