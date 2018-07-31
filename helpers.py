from PyQt5.QtWidgets import QProgressBar, QDialog, QApplication, QGridLayout, QMessageBox
from PyQt5.QtGui import QIcon

import numpy as np
import os
import time
import sys
import json


def split_location_string(location: str):
    """
    Returns only the [parent directory, filename] from full location of the file

    :param location: string: location of the file on the disk
    :return: list: [parent directory, name of the file]
    """
    return [os.path.dirname(location), os.path.basename(location)]


def get_subfolders(path):
    """
    Helper function to find all folders within folder specified by "path"

    :param path: path to folder to scrap subfolders from
    :return: list[] of subfolders from specified path
    """
    return [f.name for f in os.scandir(path) if f.is_dir() and f.name[0]]


def get_files_in_folder(path):
    """
    Helper function to find all files within folder specified by path

    :param path: path to folder to scrap files from
    :return: list[] of files from specified path
    """
    return [f.name for f in os.scandir(path) if f.is_file()]


def show_error_message(title, message):
    """
    Function for displaying warnings/errors

    :param title: Title of the displayed watning window
    :param message: Message shown by the displayed watning window
    :return: NoneType
    """
    msg_box = QMessageBox()
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setWindowIcon(QIcon("img/warning_icon.png"))
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.Ok)
    msg_box.exec_()


def is_numeric(value):
    """
    Function that quickly checks if some variable can be casted to float

    :param value: check if this can be casted to float
    :return:
    """
    try:
        float(value)
        return True
    except:
        return False


def frange(start, end, step):
    while start < end:
        yield start
        start += step


class ProgressBarWidget(QDialog):

    def __init__(self):
        super().__init__()

        self.init_ui()
        self.show()

    def init_ui(self):

        self.setWindowTitle("Procesing . . .")
        self.setGeometry(200, 200, 200, 50)
        self.grid_layout = QGridLayout()
        self.progressBar = QProgressBar()
        self.grid_layout.addWidget(self.progressBar)
        self.setLayout(self.grid_layout)

    def setValue(self, val):  # Sets value
        self.progressBar.setProperty("value", val)


def main():

    app = QApplication(sys.argv)
    ex = ProgressBarWidget()
    for i in range(0, 100):
        time.sleep(0.05)
        ex.setValue(((i + 1) / 100) * 100)
        QApplication.processEvents()
    ex.close()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()