import sqlalchemy

import db
from db import Task
from Classes.connection import Connection

CONNECTION = Connection()

class Tasks():
    def __init__(self):
        pass

    def deps_text(self, task, chat, preceed=''):
        text = ''
        for i in range(len(task.dependencies.split(',')[:-1])):
            line = preceed
            query = db.session.query(db.Task).filter_by(id=int(task.dependencies.split(',')[:-1][i]), chat=chat)
            dep = query.one()

            icon = '\U0001F195'
            if dep.status == 'DOING':
                icon = '\U000023FA'
            elif dep.status == 'DONE':
                icon = '\U00002611'

            if i + 1 == len(task.dependencies.split(',')[:-1]):
                line += '└── [[{}]] {} {} {}\n'.format(dep.id, icon, dep.name, dep.priority)
                line += self.deps_text(dep, chat, preceed + '    ')
            else:
                line += '├── [[{}]] {} {} {}\n'.format(dep.id, icon, dep.name, dep.priority)
                line += self.deps_text(dep, chat, preceed + '│   ')

            text += line

        return text

    def treatException(self, task_id, chat):
        self.query = db.session.query(db.Task).filter_by(id=task_id, chat=chat)
        try:
            self.task = self.query.one()
        except sqlalchemy.orm.exc.NoResultFound:
            CONNECTION.sendMessage("_404_ Task {} not found x.x".format(task_id), chat)
            return 1
        return self.task


    def splitDualInput(self, msg, text):
        if msg != '':
            if len(msg.split(' ', 1)) > 1:
                text = msg.split(' ', 1)[1]
            msg = msg.split(' ', 1)[0]
        return msg, text

    def createTask(self, msg, chat):
        self.task = db.Task(chat=chat, name=msg, status='TODO', dependencies='', parents='', priority='')
        db.session.add(self.task)
        db.session.commit()
        CONNECTION.sendMessage("New task *TODO* [[{}]] {}".format(self.task.id, self.task.name), chat)

    def duplicateTask(self, task_id, chat):
        self.task = self.treatException(task_id, chat)
        if self.task == 1:
            return

        self.dtask = db.Task(chat=self.task.chat, name=self.task.name, status=self.task.status, dependencies=self.task.dependencies,
                        parents=self.task.parents, priority=self.task.priority, duedate=self.task.duedate)
        db.session.add(self.dtask)

        for t in self.task.dependencies.split(',')[:-1]:
            self.qy = db.session.query(db.Task).filter_by(id=int(t), chat=chat)
            t = self.qy.one()
            t.parents += '{},'.format(self.dtask.id)

        db.session.commit()
        CONNECTION.sendMessage("New task *TODO* [[{}]] {}".format(self.dtask.id, self.dtask.name), chat)

    def moveTask(self, command, task_id, chat):
        self.task = self.treatException(task_id, chat)
        if self.task == 1:
            return
        self.task.status = command.upper()[1:]
        db.session.commit()
        CONNECTION.sendMessage("*"+self.task.status+"* task [[{}]] {}".format(self.task.id, self.task.name), chat)

    def deleteTask(self, task_id, chat):
        self.task = self.treatException(task_id, chat)
        if self.task == 1:
            return

        if self.task.parents != '':
            CONNECTION.sendMessage("There are dependencies to perform this task, finish them first", chat)
            return
        for t in self.task.dependencies.split(',')[:-1]:
            self.qy = db.session.query(db.Task).filter_by(id=int(t), chat=chat)
            t = self.qy.one()
            t.parents = t.parents.replace('{},'.format(self.task.id), '')
        db.session.delete(self.task)
        db.session.commit()
        CONNECTION.sendMessage("Task [[{}]] deleted".format(task_id), chat)

    def showTaskList(self, chat):
        self.a = ''

        self.a += '\U0001F4CB Task List\n'
        self.query = db.session.query(db.Task).filter_by(parents='', chat=chat).order_by(db.Task.id)
        for self.task in self.query.all():
            self.icon = '\U0001F195'
            if self.task.status == 'DOING':
                self.icon = '\U000023FA'
            elif self.task.status == 'DONE':
                self.icon = '\U00002611'

            self.a += '[[{}]] {} {} {}\n'.format(self.task.id, self.icon, self.task.name, self.task.priority)
            self.a += self.deps_text(self.task, chat)

        CONNECTION.sendMessage(self.a, chat)
        self.a = ''

        self.a += '\U0001F4DD _Status_\n'
        self.query = db.session.query(db.Task).filter_by(status='TODO', chat=chat).order_by(db.Task.id)
        self.a += '\n\U0001F195 *TODO*\n'
        for self.task in self.query.all():
            self.a += '[[{}]] {} {}\n'.format(self.task.id, self.task.name, self.task.priority)
        self.query = db.session.query(db.Task).filter_by(status='DOING', chat=chat).order_by(db.Task.id)
        self.a += '\n\U000023FA *DOING*\n'
        for self.task in self.query.all():
            self.a += '[[{}]] {} {}\n'.format(self.task.id, self.task.name, self.task.priority)
        self.query = db.session.query(db.Task).filter_by(status='DONE', chat=chat).order_by(db.Task.id)
        self.a += '\n\U00002611 *DONE*\n'
        for self.task in self.query.all():
            self.a += '[[{}]] {} {}\n'.format(self.task.id, self.task.name, self.task.priority)

        CONNECTION.sendMessage(self.a, chat)

    def dependson(self, text, task_id, chat):
        self.task = self.treatException(task_id, chat)
        if self.task == 1:
            return
        print(text)
        print(task_id)
        print("**************************************************************************")
        if text == '':
            for i in self.task.dependencies.split(',')[:-1]:
                i = int(i)
                self.q = db.session.query(db.Task).filter_by(id=i, chat=chat)
                self.t = self.q.one()
                self.t.parents = self.t.parents.replace('{},'.format(self.task.id), '')

            self.task.dependencies = ''
            CONNECTION.sendMessage("Dependencies removed from task {}".format(task_id), chat)
        else:
            for depid in text.split(' '):
                if not depid.isdigit():
                    CONNECTION.sendMessage("All dependencies ids must be numeric, and not {}".format(depid), chat)
                else:
                    depid = int(depid)
                    self.query = db.session.query(db.Task).filter_by(id=depid, chat=chat)
                    try:
                        self.taskdep = self.query.one()
                        self.dependencyList = self.taskdep.dependencies.split(',')
                        hasCircularDependency = False
                        if not str(self.task.id) in self.dependencyList and int(task_id) != int(text):
                            self.taskdep.parents += str(self.task.id) + ','
                        else:
                            CONNECTION.sendMessage("This task already depends on other", chat)
                            hasCircularDependency = True

                    except sqlalchemy.orm.exc.NoResultFound:
                        CONNECTION.sendMessage("_404_ Task {} not found x.x".format(depid), chat)
                        continue

                    if(hasCircularDependency == False):
                        self.deplist = self.task.dependencies.split(',')
                        if str(depid) not in self.deplist:
                            self.task.dependencies += str(depid) + ','
                        CONNECTION.sendMessage("Task {} dependencies up to date".format(task_id), chat)

        db.session.commit()

    def renameTask(self, text, task_id, chat):
        self.task = self.treatException(task_id, chat)
        if self.task == 1:
            return

        if text == '':
            CONNECTION.sendMessage("You want to modify task {}, but you didn't provide any new text".format(task_id), chat)
            return

        self.old_text = self.task.name
        self.task.name = text
        db.session.commit()
        CONNECTION.sendMessage("Task {} redefined from {} to {}".format(task_id, self.old_text, text), chat)

    def priorityTask(self, text, task_id, chat):
        self.task = self.treatException(task_id, chat)
        if self.task == 1:
            return

        if text == '':
            self.task.priority = ''
            CONNECTION.sendMessage("_Cleared_ all priorities from task {}".format(task_id), chat)
        else:
            if text.lower() not in ['high', 'medium', 'low']:
                CONNECTION.sendMessage("The priority *must be* one of the following: high, medium, low", chat)
            else:
                if text.lower() == 'high':
                    self.task.priority = '\U0001F947'
                elif text.lower() == 'medium':
                    self.task.priority = '\U0001F948'
                else:
                    self.task.priority = '\U0001F949'
                CONNECTION.sendMessage("*Task {}* priority has priority *{}*".format(task_id, text.lower()), chat)
        db.session.commit()
