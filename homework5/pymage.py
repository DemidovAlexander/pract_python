__author__ = 'Demidov'

import sys
from PySide import QtGui, QtCore


class Interface(QtGui.QMainWindow):
    maximumWidth = 700
    maximumHeight = 600

    def __init__(self):
        super(Interface, self).__init__()
        self.__initUI__()

    def __initUI__(self):
        self.setGeometry(300, 300, 300, 300)
        self.setWindowTitle('PyMage')

        self.__showLayout__()
        self.__showMenu__()

        self.show()

    def __showMenu__(self):
        openAction = QtGui.QAction('&Open', self)
        openAction.setShortcut('Ctrl+O')
        openAction.setStatusTip('Choose image file')
        openAction.triggered.connect(self.__loadImage__)

        exitAction = QtGui.QAction('&Exit', self)
        exitAction.setShortcut('Ctrl+X')
        exitAction.setStatusTip('Exit')
        exitAction.triggered.connect(self.close)

        self.statusBar()

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(openAction)
        fileMenu.addAction(exitAction)

    def __loadImage__(self):
        fileName, _ = QtGui.QFileDialog.getOpenFileName(self, 'Choose image file', '/home')
        self.pixmap = QtGui.QPixmap(fileName)

        imageProportions = self.pixmap.size().width() / self.pixmap.size().height()
        self.imageWidth = min(self.pixmap.size().width(), self.maximumWidth)
        self.imageHeight = min(self.pixmap.size().height(), self.maximumHeight - 50)

        if (imageProportions > 1):
            self.imageHeight = int(self.imageWidth / imageProportions)
        else:
            self.imageWidth = int(self.imageHeight * imageProportions)

        self.setMaximumSize(self.imageWidth, self.imageHeight + 50)
        self.resize(self.imageWidth, self.imageHeight + 50)

        self.slider.setValue((self.slider.minimum() + self.slider.maximum()) / 2)

        self.__resizeImage__()

        #почему-то активная зона слайдера располагается вверху него
        #нормально настроить не удалось, т. к. неясно, что за это отвечает
        #(способ tab+стрелки работает, а мышкой нужно наводить на самый верх слайдера)
        self.slider.resize(self.size().width(), 20)
        self.slider.move(0, self.size().height() - 25)
        self.slider.show()

        self.slider.valueChanged.connect(self.__resizeImage__)

    def __showLayout__(self):
        self.lable = QtGui.QLabel(self)
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.hide()

        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.lable)
        self.hbox.addWidget(self.slider)

        self.setLayout(self.hbox)

    def __resizeImage__(self):
        self.factor = (self.slider.value() + 1) / 100
        self.lable.setPixmap(self.pixmap.scaled(self.imageWidth * self.factor, self.imageHeight * self.factor))
        self.lable.resize(self.imageWidth * self.factor, self.imageHeight * self.factor)
        self.lable.move((self.imageWidth - self.lable.size().width()) / 2, (self.imageHeight - self.lable.size().height()) / 2 + 20)


def main():
    application = QtGui.QApplication(sys.argv)
    initInterface = Interface()
    sys.exit(application.exec_())


if __name__ == '__main__':
    main()
