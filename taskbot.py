#!/usr/bin/env python3

import time
import string
from Classes.connection import Connection
import sqlalchemy

import db
from db import Task

HELP = """
 /new NOME
 /todo ID
 /doing ID
 /done ID
 /delete ID
 /list
 /rename ID NOME
 /dependson ID ID...
 /duplicate ID
 /priority ID PRIORITY{low, medium, high}
 /help
"""

COMMANDS = [' /new ', ' /todo ', ' /doing ', ' /done ',
           ' /delete ', ' /list ', ' /rename ', ' /help ', 
           ' /dependson ', ' /duplicate ', ' /priority ']

CONNECTION = Connection()

def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def deps_text(task, chat, preceed=''):
    text = ''

    for i in range(len(task.dependencies.split(',')[:-1])):
        line = preceed
        query = db.session.query(Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
        dep = query.one()

        icon = '\U0001F195'
        if dep.status == 'DOING':
            icon = '\U000023FA'
        elif dep.status == 'DONE':
            icon = '\U00002611'

        if i + 1 == len(task.dependencies.split(',')[:-1]):
            line += '└── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '    ')
        else:
            line += '├── [[{}]] {} {}\n'.format(dep.id, icon, dep.name)
            line += deps_text(dep, chat, preceed + '│   ')

        text += line

    return text

def treatException(task_id, chat):
    query = db.session.query(Task).filter_by(id=task_id, chat=chat)
    try:
        task = query.one()
    except sqlalchemy.orm.exc.NoResultFound:
        CONNECTION.sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
        return 1
    return task
def splitDualInput(msg, text):    
    if msg != '':
        if len(msg.split(' ', 1)) > 1:
            text = msg.split(' ', 1)[1]
        msg = msg.split(' ', 1)[0]
    return msg, text

def createTask(msg, chat):
    task = Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
    db.session.add(task)
    db.session.commit()
    CONNECTION.sendMessage("New task *TODO* [[{}]] {}".format(task.id, task.name), chat)

def duplicateTask(task_id, chat):
    task = treatException(task_id, chat)
    if task == 1:
        return

    dtask = Task(chat=task.chat, name=task.name, status=task.status, dependencies=task.dependencies,
                    parents=task.parents, priority=task.priority, duedate=task.duedate)
    db.session.add(dtask)

    for t in task.dependencies.split(',')[:-1]:
        qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
        t = qy.one()
        t.parents += '{},'.format(dtask.id)

    db.session.commit()
    CONNECTION.sendMessage("New task *TODO* [[{}]] {}".format(dtask.id, dtask.name), chat)

def moveTask(command, task_id, chat):
    task = treatException(task_id, chat)
    if task == 1:
        return
    task.status = command.upper()[1:]
    db.session.commit()
    CONNECTION.sendMessage("*"+task.status+"* task [[{}]] {}".format(task.id, task.name), chat)

def deleteTask(task_id, chat):

    task = treatException(task_id, chat)
    if task == 1:
        return
        
    for t in task.dependencies.split(',')[:-1]:
        qy = db.session.query(Task).filter_by(id=int(t), chat=chat)
        t = qy.one()
        t.parents = t.parents.replace('{},'.format(task.id), '')
    db.session.delete(task)
    db.session.commit()
    CONNECTION.sendMessage("Task [[{}]] deleted".format(task_id), chat)

def showTaskList(chat):
    a = ''

    a += '\U0001F4CB Task List\n'
    query = db.session.query(Task).filter_by(parents='', chat=chat).order_by(Task.id)
    for task in query.all():
        icon = '\U0001F195'
        if task.status == 'DOING':
            icon = '\U000023FA'
        elif task.status == 'DONE':
            icon = '\U00002611'

        a += '[[{}]] {} {}\n'.format(task.id, icon, task.name)
        a += deps_text(task, chat)

    CONNECTION.sendMessage(a, chat)
    a = ''

    a += '\U0001F4DD _Status_\n'
    query = db.session.query(Task).filter_by(status='TODO', chat=chat).order_by(Task.id)
    a += '\n\U0001F195 *TODO*\n'
    for task in query.all():
        a += '[[{}]] {}\n'.format(task.id, task.name)
    query = db.session.query(Task).filter_by(status='DOING', chat=chat).order_by(Task.id)
    a += '\n\U000023FA *DOING*\n'
    for task in query.all():
        a += '[[{}]] {}\n'.format(task.id, task.name)
    query = db.session.query(Task).filter_by(status='DONE', chat=chat).order_by(Task.id)
    a += '\n\U00002611 *DONE*\n'
    for task in query.all():
        a += '[[{}]] {}\n'.format(task.id, task.name)

    CONNECTION.sendMessage(a, chat)

def dependson(text, task_id, chat):
    task = treatException(task_id, chat)
    if task == 1:
        return

    if text == '':
        for i in task.dependencies.split(',')[:-1]:
            i = int(i)
            q = db.session.query(Task).filter_by(id=i, chat=chat)
            t = q.one()
            t.parents = t.parents.replace('{},'.format(task.id), '')

        task.dependencies = ''
        CONNECTION.sendMessage("Dependencies removed from task {}".format(task_id), chat)
    else:
        for depid in text.split(' '):
            if not depid.isdigit():
                CONNECTION.sendMessage("All dependencies ids must be numeric, and not {}".format(depid), chat)
            else:
                depid = int(depid)
                query = db.session.query(Task).filter_by(id=depid, chat=chat)
                try:
                    taskdep = query.one()
                    taskdep.parents += str(task.id) + ','
                except sqlalchemy.orm.exc.NoResultFound:
                    CONNECTION.sendMessage("_404_ Task {} not found x.x".format(depid), chat)
                    continue

                deplist = task.dependencies.split(',')
                if str(depid) not in deplist:
                    task.dependencies += str(depid) + ','

    db.session.commit()
    CONNECTION.sendMessage("Task {} dependencies up to date".format(task_id), chat)

def renameTask(text, task_id, chat):
    task = treatException(task_id, chat)
    if task == 1:
        return

    if text == '':
        CONNECTION.sendMessage("You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
        return
                    
    old_text = task.name
    task.name = text
    db.session.commit()
    CONNECTION.sendMessage("Task {} redefined from {} to {}".format(task_id, old_text, text), chat)

def priorityTask(text, task_id, chat):
    task = treatException(task_id, chat)
    if task == 1:
        return

    if text == '':
        task.priority = ''
        CONNECTION.sendMessage("_Cleared_ all priorities from task {}".format(task_id), chat)
    else:
        if text.lower() not in ['high', 'medium', 'low']:
            CONNECTION.sendMessage("The priority *must be* one of the following: high, medium, low", chat)
        else:
            task.priority = text.lower()
            CONNECTION.sendMessage("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
    db.session.commit() 

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
            createTask(msg, chat)

        elif command == '/list':
            showTaskList(chat)

        elif command == '/start':
            CONNECTION.sendMessage("Welcome! Here is a list of things you can do.", chat)
            CONNECTION.sendMessage(HELP, chat)
            
        elif command == '/help':
            CONNECTION.sendMessage("Here is a list of things you can do.", chat)
            CONNECTION.sendMessage(HELP, chat)


        else: 
            if command in ['/dependson', '/priority', '/rename']:
                text = ''
                msg, text = splitDualInput(msg, text)

            if not msg.isdigit():
                CONNECTION.sendMessage("You must inform the task id", chat)

            else:
                task_id = int(msg)

                if command == '/duplicate':
                    duplicateTask(task_id, chat)

                elif command == '/delete':
                    deleteTask(task_id, chat)

                elif command == '/todo':
                    moveTask(command, task_id, chat)

                elif command == '/doing':
                    moveTask(command, task_id, chat)

                elif command == '/done':
                    moveTask(command, task_id, chat)

                elif command == '/rename':
                    renameTask(text, task_id, chat)

                elif command == '/priority':
                    priorityTask(text, task_id, chat)

                elif command == '/dependson':
                    dependson(text, task_id, chat)
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
