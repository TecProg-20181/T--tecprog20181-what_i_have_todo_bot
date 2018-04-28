TOKEN = "tokenBot.txt"
URL = "https://api.telegram.org/bot{}/"

class Token():

    def __init__(self):
        self.inFile = None
        self.fileLine = None
    
    def readToken(self):
        self.inFile = open(TOKEN, 'r')
        self.fileLine = self.inFile.readline()
        return URL.format(self.fileLine.rstrip())

    def getToken(self):
        return self.readToken()