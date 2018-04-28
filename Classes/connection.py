from Classes.token import Token
import requests
import json
import urllib

URL = Token().getToken()

class Connection():
    def __init__(self):
        self.response = ''
        self.content = ''
        self.js = ''
        self.url = ''

    def getUrl(self, url):
        self.response = requests.get(url)
        self.content = self.response.content.decode("utf8")
        return self.content

    def getJsonFromUrl(self, url):
        self.content = self.getUrl(url)
        self.js = json.loads(self.content)
        return self.js

    def getUpdates(self, offset=None):
        self.url = URL + "getUpdates?timeout=100"
        if offset:
            self.url += "&offset={}".format(offset)
        self.js = self.getJsonFromUrl(self.url)
        return self.js

    def sendMessage(self, text, chat_id, reply_markup=None):
        text = urllib.parse.quote_plus(text)
        self.url = URL + "sendMessage?text={}&chat_id={}&parse_mode=Markdown".format(text, chat_id)
        if reply_markup:
            self.url += "&reply_markup={}".format(reply_markup)
        self.getUrl(self.url)

