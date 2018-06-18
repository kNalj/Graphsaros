from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QDesktopWidget, QPushButton, QWidget, QTableView, \
    QTextBrowser
from PyQt5 import QtCore, QtGui, QtWidgets

import sys


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # define title of the window
        self.title = "Graphsaros"
        # define width of the window
        self.width = 840
        # define height of th window
        self.height = 460

        # QMainWindow by default has defined layout which defines central widget as a place where
        # to add your widgets (buttons, text, etc.), so in order to be able to customize it we
        # to create central widget and set grid layout to it, then we can do what we want
        self.centralWidget = QWidget()

        # call to a method that build user interface
        self.init_ui()
        # after the interface has been built, show the window
        self.show()

    def init_ui(self):

        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        # set position of the window relative to the dimensions of the display screen
        self.setGeometry(int(0.02 * width), int(0.05 * height), self.width, self.height)
        # set the title of the window
        self.setWindowTitle(self.title)
        # set the icon of the window
        self.setWindowIcon(QtGui.QIcon("img/graph.png"))

        # define the layout for central widget
        self.grid_layout = QGridLayout()
        self.add_to_list_btn = QPushButton("Add to list")
        self.exit_btn = QPushButton("Exit")
        self.open_dataset_btn = QPushButton("Open")
        self.opened_datasets_tableview = QTableView()
        self.selected_dataset_textbrowser = QTextBrowser()

        self.grid_layout.addWidget(self.add_to_list_btn, 1, 1, 1, 2)
        self.grid_layout.addWidget(self.open_dataset_btn, 2, 1, 1, 1)
        self.grid_layout.addWidget(self.exit_btn, 2, 2, 1, 1)
        self.grid_layout.addWidget(self.opened_datasets_tableview, 0, 1, 1, 2)
        self.grid_layout.addWidget(self.selected_dataset_textbrowser, 0, 0, 3, 1)

        self.centralWidget.setLayout(self.grid_layout)
        self.setCentralWidget(self.centralWidget)


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
