from PyQt5.QtWidgets import QProgressBar, QDialog, QApplication, QGridLayout, QMessageBox, QWidget, QDesktopWidget, \
    QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QGroupBox
from PyQt5.QtGui import QIcon

import numpy as np
import os
import time
import sys
import json
import graphs


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


class EditAxisWidget(QWidget):
    def __init__(self, window):
        super(EditAxisWidget, self).__init__()

        self.window = window

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Edit axis data")
        self.setWindowIcon(QIcon("img/dataStructure.png"))

        layout = QGridLayout()

        if isinstance(self.window, graphs.LineTrace.LineTrace):
            pass
        elif isinstance(self.window, graphs.Heatmap.Heatmap):
            for element in ["main_subplot", "line_trace_graph"]:
                box = QGroupBox(self)
                h_layout = QHBoxLayout()
                plot_label = QLabel(element.capitalize().replace("_", " "), self)
                layout.addWidget(plot_label)

                for side in ('left', 'bottom'):
                    # this one contains all elements of one axis of one plot
                    v_layout = QVBoxLayout()

                    axis = self.window.plot_elements[element].getAxis(side)

                    plot_axis_text = axis.labelText
                    plot_text = QLineEdit(plot_axis_text)
                    plot_current_unit = axis.labelUnits
                    plot_unit = QLineEdit(plot_current_unit)
                    plot_current_font_size = axis.labelStyle["font-size"]
                    plot_font_size = QLineEdit(plot_current_font_size)
                    tick_spacing_major = QLineEdit()
                    tick_spacing_major.setPlaceholderText("Major ticks")
                    tick_spacing_minor = QLineEdit()
                    tick_spacing_minor.setPlaceholderText("Minor ticks")
                    tick_h_layout = QHBoxLayout()
                    tick_h_layout.addWidget(tick_spacing_major)
                    tick_h_layout.addWidget(tick_spacing_minor)

                    v_layout.addWidget(QLabel(side.capitalize()))
                    v_layout.addWidget(plot_text)
                    v_layout.addWidget(plot_unit)
                    v_layout.addWidget(plot_font_size)
                    v_layout.addLayout(tick_h_layout)
                    h_layout.addLayout(v_layout)

                box.setLayout(h_layout)
                layout.addWidget(box)

            plot_label = QLabel("Histogram")
            layout.addWidget(plot_label)

            hist_axis = self.window.plot_elements["histogram"].axis
            box = QGroupBox()
            h_layout = QHBoxLayout()
            v_layout = QVBoxLayout()
            plot_axis_text = hist_axis.labelText
            plot_text = QLineEdit(plot_axis_text)
            plot_current_unit = hist_axis.labelUnits
            plot_unit = QLineEdit(plot_current_unit)
            plot_current_font_size = hist_axis.labelStyle["font-size"]
            plot_font_size = QLineEdit(plot_current_font_size)
            tick_spacing_major = QLineEdit()
            tick_spacing_major.setPlaceholderText("Major ticks")
            tick_spacing_minor = QLineEdit()
            tick_spacing_minor.setPlaceholderText("Minor ticks")
            tick_h_layout = QHBoxLayout()
            tick_h_layout.addWidget(tick_spacing_major)
            tick_h_layout.addWidget(tick_spacing_minor)
            v_layout.addWidget(QLabel("Left"))
            v_layout.addWidget(plot_text)
            v_layout.addWidget(plot_unit)
            v_layout.addWidget(plot_font_size)
            v_layout.addLayout(tick_h_layout)
            h_layout.addLayout(v_layout)
            box.setLayout(h_layout)
            layout.addWidget(box)

        self.setLayout(layout)
        self.show()


class InfoWidget(QWidget):
    def __init__(self, buffer):
        super(InfoWidget, self).__init__()

        self.buffer = buffer

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.show()

def main():

    app = QApplication(sys.argv)
    """ex = ProgressBarWidget()
    for i in range(0, 100):
        time.sleep(0.05)
        ex.setValue(((i + 1) / 100) * 100)
        QApplication.processEvents()
    ex.close()"""
    ex = EditAxisWidget("")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()