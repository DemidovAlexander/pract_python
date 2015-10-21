__author__ = 'Demidov'

import pickle
import socket
import threading
import sys

HOST, PORT = 'localhost', 8080
MAX_BUF_SIZE = 4096
MAX_LISTENERS_IN_QUEUE = 1
REQUIRED_ARGUMENTS_NUMBER = 2


def abort_prg(error):
    print(error.join('\n'))
    sys.exit(1)


def check_parameters():
    if (len(sys.argv) > REQUIRED_ARGUMENTS_NUMBER):
        abort_prg('too many parameters')
    elif (len(sys.argv) < REQUIRED_ARGUMENTS_NUMBER):
        abort_prg('too few parameters')


class ServerThread(threading.Thread):
    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.server.bind((HOST, PORT))
            self.server.listen(MAX_LISTENERS_IN_QUEUE)

            self.serve()
        finally:
            self.server.close()

    def serve(self):
        channel, details = self.server.accept()
        try:
            while True:
                data = channel.recv(MAX_BUF_SIZE)
                if data:
                    message = pickle.loads(data)
                    channel.send(pickle.dumps(message.upper()))
        finally:
            channel.close()


class ClientThread(threading.Thread):
    def run(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client.connect((HOST, PORT))

            self.work()
        finally:
            self.client.close()

    def work(self):
        try:
            file = open(sys.argv[1], 'rt')
        except IOError:
            abort_prg('wrong filename: ' + sys.argv[1])

        try:
            self.client.sendall(pickle.dumps(file.read()))
        finally:
            file.close()

        while True:
            data = self.client.recv(MAX_BUF_SIZE)
            if data:
                print(pickle.loads(data))


if __name__ == '__main__':
    check_parameters()

    ServerThread().start()
    ClientThread().start()











