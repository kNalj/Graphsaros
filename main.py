from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QDesktopWidget, QPushButton, QWidget, QTableWidget,\
    QTextBrowser, QAction, QMenu, QFileDialog, QHeaderView, QTableWidgetItem
from PyQt5 import QtCore, QtGui, QtWidgets

import pyqtgraph as pg
import numpy as np

from LineTrace import LineTrace

import sys
import os

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")

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

        # call to a method that builds user interface
        self.init_ui()
        # call to a method that builds menu bar
        self.init_manu_bar()
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

        # create elements of the central widget
        self.add_to_list_btn = QPushButton("Add to list")
        self.add_to_list_btn.clicked.connect(self.open_file_dialog)

        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.exit)

        self.open_dataset_btn = QPushButton("Open")
        self.open_dataset_btn.clicked.connect(self.display_dataset)

        self.opened_datasets_tablewidget = QTableWidget(0, 3)
        self.opened_datasets_tablewidget.setHorizontalHeaderLabels(("Name", "Location", "Delete"))
        header = self.opened_datasets_tablewidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.opened_datasets_tablewidget.setSelectionBehavior(QTableWidget.SelectRows)

        self.selected_dataset_textbrowser = QTextBrowser()

        # position the elements within the grid layout
        self.grid_layout.addWidget(self.add_to_list_btn, 1, 1, 1, 2)
        self.grid_layout.addWidget(self.open_dataset_btn, 2, 1, 1, 1)
        self.grid_layout.addWidget(self.exit_btn, 2, 2, 1, 1)
        self.grid_layout.addWidget(self.opened_datasets_tablewidget, 0, 1, 1, 2)
        self.grid_layout.addWidget(self.selected_dataset_textbrowser, 0, 0, 3, 1)

        # set the layout of the central widget
        self.centralWidget.setLayout(self.grid_layout)
        # set central widget to be THE CENTRAL WIDGET (QMainWindow predefind element)
        self.setCentralWidget(self.centralWidget)

    def init_manu_bar(self):

        # create action for closing the program
        exit_action = QAction("&Exit", self)
        # add shortcut to this action
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        # connect action to exit method
        exit_action.triggered.connect(self.exit)

        open_action = QMenu("&Open", self)

        open_qcodes = QAction("&Open QCoDeS", self)
        open_qcodes.triggered.connect(lambda: self.open("qcodes"))
        open_qtlab = QAction("&Open QtLab", self)
        open_qtlab.triggered.connect(lambda: self.open("qtlab"))
        open_matrix = QAction("&Open matrix", self)
        open_matrix.triggered.connect(lambda: self.open("matrix"))

        open_action.addAction(open_qcodes)
        open_action.addAction(open_qtlab)
        open_action.addAction(open_matrix)

        # create menu bar
        menu_bar = self.menuBar()
        # add submenu
        file_menu = menu_bar.addMenu("&File")
        # add action to the FILE submenu
        file_menu.addMenu(open_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    @QtCore.pyqtSlot()
    def exit(self):
        app = QtGui.QGuiApplication.instance()
        app.closeAllWindows()
        self.close()

    def closeEvent(self, *args, **kwargs):
        self.exit()

    def open_file_dialog(self):
        file_dialog = QFileDialog.getOpenFileNames()

        for file in file_dialog[0]:
            name = os.path.basename(file)
            rows = self.opened_datasets_tablewidget.rowCount()
            self.opened_datasets_tablewidget.insertRow(rows)
            name_item = QTableWidgetItem(name)
            name_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.opened_datasets_tablewidget.setItem(rows, 0, name_item)
            location_item = QTableWidgetItem(file)
            location_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.opened_datasets_tablewidget.setItem(rows, 1, location_item)
            delete_current_file_btn = QPushButton("Delete")
            delete_current_file_btn.clicked.connect(self.make_delete_file_from_list(name_item))
            self.opened_datasets_tablewidget.setCellWidget(rows, 2, delete_current_file_btn)

    def display_dataset(self):
        row = self.opened_datasets_tablewidget.currentRow()
        if row != -1:
            item = self.opened_datasets_tablewidget.item(row, 1)
            location = item.text()
            with open(location, "r") as file:
                data = file.read()
                self.selected_dataset_textbrowser.clear()
                self.selected_dataset_textbrowser.append(data)
            with open(location, "r") as file:
                data = []
                for i, line in enumerate(file):
                    if i == 2:  # this line contains the format of the data matrix
                        matrix_dimensions = [int(number) for number in line[2:].strip("\n").split("\t")]
                        print(matrix_dimensions)
                    if line[0] != "#":
                        array = line.strip('\n').split('\t')
                        if array != [""]:
                            float_array = [float(value) for value in array]
                            data.append(float_array)

            # this is how you draw 2D
            x_data = [arr[0] for arr in data]
            y_data = [arr[1] for arr in data]
            self.lt = LineTrace(x_data, y_data)

    def open(self, file_type: str):
        print(file_type)

    def make_delete_file_from_list(self, name):

        def delete_file_from_list():
            self.opened_datasets_tablewidget.removeRow(self.opened_datasets_tablewidget.row(name))

        return delete_file_from_list


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
