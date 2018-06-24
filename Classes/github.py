import os
import json
import requests

from Classes.connection import Connection
CONNECTION = Connection()

class GitHub():

    def __init__(self):
        self.repo_owner = 'TecProg-20181'
        self.repo_name = 'What_i_have_todo_bot'
    
    def loginGit(self):
        f = open('login.txt', 'r')
        self.login = f.read().split('\n')

    def github_issue(self, title, chat):
        url = 'https://api.github.com/repos/%s/%s/issues' % (self.repo_owner, self.repo_name)
        session = requests.Session()
        self.loginGit()
        session.auth = (self.login[0], self.login[1])
        issue = {'title': title}
        postIssue = session.post(url, json.dumps(issue))
        if postIssue.status_code == 201:
            CONNECTION.sendMessage('Successfully created Issue {0:s}'.format(title), chat)
        else:
            CONNECTION.sendMessage('Could not create Issue {0:s}'.format(title), chat)
