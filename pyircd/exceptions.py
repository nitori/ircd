

class IrcError(Exception):
    def __init__(self, number, message=None):
        self.number = number
        self.message = message

    def __str__(self):
        return self.message