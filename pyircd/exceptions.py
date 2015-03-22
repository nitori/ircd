

class IrcError(Exception):
    def __init__(self, number, params=None):
        self.number = number
        self.params = params

    def __str__(self):
        return ' '.join(self.params)