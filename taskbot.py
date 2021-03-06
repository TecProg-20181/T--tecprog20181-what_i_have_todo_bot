#!/usr/bin/env python3

import time
import string
from Classes.connection import Connection
from Classes.task import Tasks
from Classes.github import GitHub

import db
from db import Task

HELP = """
 /new NOME
 /setDuedate ID DUEDATE
 /todo ID(s)
 /doing ID(s)
 /done ID(s)
 /delete ID(s)
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /help
"""

COMMANDS = [' /new ', ' /setDuedate ', ' /todo ', ' /doing ', ' /done ',
           ' /delete ', ' /list ', ' /rename ', ' /help ',
           ' /dependson ', ' /duplicate ', ' /priority ']

CONNECTION = Connection()
TASK = Tasks()
GITHUB = GitHub()

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def splitDualInput(msg, text):
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]
    return msg, text



def gettingMessage(update):
    if 'message' in update:
        message = update['message']
    elif 'edited_message' in update:
        message = update['edited_message']
    else:
        print('Can\'t process! {}'.format(update))
        return

    command = message["text"].split(" ", 1)[0]
    msg = ''
    if len(message["text"].split(" ", 1)) > 1:
        msg = message["text"].split(" ", 1)[1].strip()

    chat = message["chat"]["id"]

    return {'command':command, 'msg':msg ,'chat':chat }

def handle_updates(updates):
    for update in updates["result"]:
        newMessage = gettingMessage(update)

        command = newMessage.get('command')
        msg = newMessage.get('msg')
        chat = newMessage.get('chat')

        print(command, msg, chat)

        if ' '+command+' ' not in COMMANDS:
            CONNECTION.sendMessage("I'm sorry dave. I'm afraid I can't do that.", chat)
            return

        elif command == '/new':
            TASK.createTask(msg, chat)
            GITHUB.github_issue(msg, chat)


        elif command == '/list':
            TASK.showTaskList(chat)

        elif command == '/start':
            CONNECTION.sendMessage("Welcome! Here is a list of things you can do.", chat)
            CONNECTION.sendMessage(HELP, chat)

        elif command == '/help':
            CONNECTION.sendMessage("Here is a list of things you can do.", chat)
            CONNECTION.sendMessage(HELP, chat)


        else:
            if command in ['/dependson', '/priority', '/rename', '/setDuedate']:
                text = ''
                msg, text = splitDualInput(msg, text)
            try:
                task_id = list(map(int, msg.split(' ')))
            except:
                CONNECTION.sendMessage("You must inform the task id", chat)
                return
            if command == '/duplicate':
                TASK.duplicateTask(task_id[0], chat)

            elif command == '/delete':
                TASK.deleteTask(task_id, chat)

            elif command in ['/todo', '/doing', '/done']:
                TASK.moveTask(command, task_id, chat)

            elif command == '/rename':
                TASK.renameTask(text, task_id[0], chat)

            elif command == '/priority':
                TASK.priorityTask(text, task_id[0], chat)

            elif command == '/setDuedate':
                TASK.setDuedate(text, task_id[0], chat)

            elif command == '/dependson':
                TASK.dependson(text, task_id[0], chat)

def main():
    last_update_id = None
    while True:
        print("Updates")
        updates = CONNECTION.getUpdates(last_update_id)

        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)

        time.sleep(0.5)


if __name__ == '__main__':
    main()
