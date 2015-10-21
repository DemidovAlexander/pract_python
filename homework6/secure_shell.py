__author__ = 'Demidov'

import socket
import threading
import sys
import socketserver
import tempfile
import hashlib
import random

HOST, PORT = 'localhost', 8084
MAX_BUF_SIZE = 4096
MIN_ARGUMENTS_NUMBER = 2

clientsBase = {}
baseLock = threading.Lock()


def abort_prg(error):
    print(error.join('\n'))
    sys.exit(1)


#при запуске команды, посылаемые клиентами серверу,
#необходимо указать в аргументах программы
def check_parameters():
    if (len(sys.argv) < MIN_ARGUMENTS_NUMBER):
        abort_prg('too few parameters')


def getMD5sum(value):
    code = hashlib.md5()
    code.update(bytes(value, 'utf-8'))
    return code.hexdigest()


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        if not self.authorization():
            return

        import subprocess

        self.command = str(self.request.recv(MAX_BUF_SIZE), 'utf-8').strip()

        file = tempfile.TemporaryFile()
        subprocess.call(self.command.split(), stdout = file, shell = True)

        file.seek(0)
        self.request.sendall(bytes(file.read()))

    def authorization(self):
        login = str(self.request.recv(MAX_BUF_SIZE), 'utf-8')
        self.request.sendall(bytes('input password', 'utf-8'))
        password = str(self.request.recv(MAX_BUF_SIZE), 'utf-8')

        baseLock.acquire()
        try:
            if clientsBase.setdefault(login) == getMD5sum(password):
                self.request.sendall(bytes('ok', 'utf-8'))
                return True
            else:
                self.request.sendall(bytes('wrong password', 'utf-8'))
                return False
        finally:
            baseLock.release()


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class Server(threading.Thread):
    def run(self):
        server = ThreadedTCPServer((HOST, PORT), MyTCPHandler)
        server.serve_forever()

    def registerClient(self, login, password):
        baseLock.acquire()
        try:
            if clientsBase.setdefault(login) == None:
                clientsBase[login] = getMD5sum(password)
        finally:
            baseLock.release()


class ClientThread(threading.Thread):
    def __init__(self, command, login, password):
        self.command = command
        self.login = login
        self.password = password
        super(ClientThread, self).__init__()

    def run(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))

            self.work()
        finally:
            self.client.close()

    def authorization(self):
        self.client.sendall(bytes(self.login, 'utf-8'))

        answer = self.client.recv(MAX_BUF_SIZE)
        if answer and (str(answer, 'utf-8') == 'input password'):
            self.client.sendall(bytes(self.password, 'utf-8'))

            answer = self.client.recv(MAX_BUF_SIZE)
            if answer and (str(answer, 'utf-8') == 'ok'):
                return True
            else:
                return False

    def work(self):
        if not self.authorization():
            return

        self.client.sendall(bytes(self.command, 'utf-8'))

        while True:
            data = self.client.recv(MAX_BUF_SIZE)
            if data:
                print(str(data, 'utf-8'))


def get_random_password():
    return str(random.random())


if __name__ == '__main__':
    check_parameters()

    server = Server()
    server.start()

    for commandNumber in range(len(sys.argv) - 1):
        password = get_random_password()
        server.registerClient(str(commandNumber), password)
        ClientThread(sys.argv[commandNumber + 1], str(commandNumber), password).start()











