class Blog:
    def __init__(self):
        self.storage = {}

    def add_post(self, op, username, title, content):
        if username not in self.storage:
            self.storage[username] = []
        self.storage[username].append((op, title, content))