__author__ = 'Demidov'

import sys
import threading
from PySide import QtGui


class Interface(QtGui.QMainWindow):
    listIPs = []
    fileName = ''

    def __init__(self):
        super(Interface, self).__init__()
        self.__initUI__()

    def __initUI__(self):
        self.statusBar().showMessage('waiting input')
        self.__chooseFile__()
        self.__inputIPs__()

        self.setGeometry(300, 300, 340, 200)
        self.setWindowTitle('Pinger')
        self.show()

    def __chooseFile__(self):
        self.button = QtGui.QPushButton('Browse', self)
        self.button.move(220, 30)
        self.button.clicked.connect(self.__showDialog__)

        self.lineEdit = QtGui.QLineEdit(self)
        self.lineEdit.resize(180, 30)
        self.lineEdit.move(20, 32)

        self.lable = QtGui.QLabel(self)
        self.lable.setFont(QtGui.QFont('Arial', 10))
        self.lable.setText('Choose output file')
        self.lable.adjustSize()
        self.lable.move(20, 16)

    def __showDialog__(self):
        self.fileName, _ = QtGui.QFileDialog.getOpenFileName(self, 'Choose output file', '/home')
        self.lineEdit.setText(str(self.fileName))

    def __inputIPs__(self):
        self.button = QtGui.QPushButton('Ping', self)
        self.button.move(220, 90)
        self.button.clicked.connect(self.__ping__)

        self.lable = QtGui.QLabel(self)
        self.lable.setFont(QtGui.QFont('Arial', 10))
        self.lable.setText('Input space separated IPs')
        self.lable.adjustSize()
        self.lable.move(20, 76)

        lineEdit = QtGui.QLineEdit(self)
        lineEdit.resize(180, 30)
        lineEdit.move(20, 92)

        lineEdit.textChanged[str].connect(self.__onChanged__)

    def __onChanged__(self, text):
        self.listIPs = text.split()

    def __ping__(self):
        try:
            self.statusBar().showMessage('proceeding')
            pinger(self.listIPs, self.fileName)
        except IOError as error:
            self.statusBar().showMessage(str(error))
        else:
            self.statusBar().showMessage('ready')


def printError(error):
    raise IOError(error)


def check_parameters(parameters):
    if (len(parameters) == 0):
        printError('too few parameters')

    for current_ip in parameters:
        import re
        ip_expression = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')
        if not(ip_expression.match(current_ip)):
            printError('wrong ip: ' + current_ip)


def ping_ip(ip, file_lock, file):
    import subprocess
    result = subprocess.call(["ping", '-n', '1', ip], stdout = subprocess.PIPE)

    file_lock.acquire()
    try:
        if result == 0:
            file.write(ip + '\n')
    finally:
        file_lock.release()


def pinger(parameters, fileName):
    check_parameters(parameters)

    try:
        file = open(fileName, 'w')
    except IOError:
        printError('wrong filename: ' + fileName)

    file_lock = threading.Lock()
    threads = []
    for current_ip in parameters:
        threads.append(threading.Thread(target = ping_ip, args = (current_ip, file_lock, file)))
        threads[-1].start()

    for current_ip in threads:
        current_ip.join()

    file.close()


def main():
    application = QtGui.QApplication(sys.argv)
    initInterface = Interface()
    sys.exit(application.exec_())


if __name__ == '__main__':
    main()















