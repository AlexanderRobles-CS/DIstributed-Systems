class Blog:
    def __init__(self):                         # container for blog posts
        self.blogBin = {}

    def commitPost(self, operation, user, title, contents):        # add post to blog
        if user not in self.blogBin: 
            self.blogBin[user] = []

        self.blogBin[user].append((operation, title, contents))