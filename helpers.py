from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QIcon, QValidator

import os
import ntpath
import numpy as np


def split_location_string(location: str):
    """
    Returns only the [parent directory, filename] from full location of the file

    :param location: string: location of the file on the disk
    :return: list: [parent directory, name of the file]
    """
    return [os.path.dirname(location), os.path.basename(location)]


def get_location_basename(location: str):
    head, tail = ntpath.split(location)
    return tail or ntpath.basename(head)


def get_location_path(location: str):
    head, tail = ntpath.split(location)
    if tail:
        return head
    return ntpath.dirname(head)


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


def shift(arr, num, fill_value=0):
    result = np.empty_like(arr)
    if num > 0:
        result[:num] = fill_value
        result[num:] = arr[:-num]
    elif num < 0:
        result[num:] = fill_value
        result[:num] = arr[-num:]
    else:
        result = arr
    return result


def check_validator_state(sender, *args, **kwargs):
    validator = sender.validator()
    state = validator.validate(sender.text(), 0)[0]

    if state == QValidator.Acceptable:
        color = '#c4df9b'  # green
    elif state == QValidator.Intermediate:
        color = '#fff79a'  # yellow
    else:
        color = '#f6989d'  # red
    sender.setStyleSheet('QLineEdit { background-color: %s }' % color)


def main():
    print("End of test")


if __name__ == '__main__':
    main()
