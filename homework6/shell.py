__author__ = 'Demidov'

import socket
import threading
import sys
import socketserver
import tempfile

HOST, PORT = 'localhost', 8084
MAX_BUF_SIZE = 4096
MIN_ARGUMENTS_NUMBER = 2


def abort_prg(error):
    print(error.join('\n'))
    sys.exit(1)


#при запуске команды, посылаемые клиентами серверу,
#необходимо указать в аргументах программы
def check_parameters():
    if (len(sys.argv) < MIN_ARGUMENTS_NUMBER):
        abort_prg('too few parameters')


class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        import subprocess

        self.command = str(self.request.recv(MAX_BUF_SIZE), 'utf-8').strip()

        file = tempfile.TemporaryFile()
        subprocess.call(self.command.split(), stdout = file, shell = True)

        file.seek(0)
        self.request.sendall(bytes(file.read()))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    pass


class ServerThread(threading.Thread):
    def run(self):
        server = ThreadedTCPServer((HOST, PORT), MyTCPHandler)
        server.serve_forever()


class ClientThread(threading.Thread):
    def __init__(self, command):
        self.command = command
        super(ClientThread, self).__init__()

    def run(self):
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((HOST, PORT))

            self.work()
        finally:
            self.client.close()

    def work(self):
        self.client.sendall(bytes(self.command, 'utf-8'))

        while True:
            data = self.client.recv(MAX_BUF_SIZE)
            if data:
                print(str(data, 'utf-8'))

if __name__ == '__main__':
    check_parameters()

    ServerThread().start()

    for command in sys.argv[1:]:
        ClientThread(command).start()











