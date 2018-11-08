from PyQt5.QtWidgets import QProgressBar, QDialog, QApplication, QGridLayout, QMessageBox, QWidget, QDesktopWidget, \
    QLabel, QLineEdit, QHBoxLayout, QVBoxLayout, QGroupBox, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, QObject


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
    """
    Base class for widget that displays buffer info

    Buffer info is:
        dimensions: dimensions of the matrix
        x axis: start, end, steps
        y axis: start, end, steps
    """
    submitted = pyqtSignal(object)

    def __init__(self):
        super(EditAxisWidget, self).__init__()

    def init_ui(self):
        """
        Should be implemented in the child classes
        :return:
        """
        raise NotImplementedError

    def data_submitted(self):
        """
        Should be implemented in the child classes
        :return:
        """
        raise NotImplementedError

    def validate(self):
        """
        Should be implemented in the child classes.
        Checks if data submitted is correct.

        :return: boolean: True if data is valid, False if data is not valid
        """
        raise NotImplementedError


class Edit2DAxisWidget(EditAxisWidget):
    def __init__(self):
        super(Edit2DAxisWidget, self).__init__()

    def init_ui(self):
        pass

    def data_submitted(self):
        pass

    def validate(self):
        pass


class Edit3DAxisWidget(EditAxisWidget):
    def __init__(self, window):
        super(Edit3DAxisWidget, self).__init__()

        # Reference to a window that is being changed
        self.window = window

        self.elements = {}

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Edit axis data")
        self.setWindowIcon(QIcon("img/dataStructure.png"))

        layout = QGridLayout()

        for element in ["main_subplot", "line_trace_graph"]:
            box = QGroupBox(self)
            h_layout = QHBoxLayout()
            plot_label = QLabel(element.capitalize().replace("_", " "), self)
            layout.addWidget(plot_label)
            self.elements[element] = {}

            for side in ('left', 'bottom'):
                self.elements[element][side] = {}
                # this one contains all elements of one axis of one plot
                v_layout = QVBoxLayout()

                axis = self.window.plot_elements[element].getAxis(side)

                plot_axis_text = axis.labelText
                plot_text = QLineEdit(plot_axis_text)
                plot_text.setPlaceholderText("Label")
                self.elements[element][side]["label"] = plot_text
                plot_current_unit = axis.labelUnits
                plot_unit = QLineEdit(plot_current_unit)
                plot_unit.setPlaceholderText("Unit")
                self.elements[element][side]["unit"] = plot_unit
                plot_current_font_size = axis.labelStyle["font-size"]
                plot_font_size = QLineEdit(plot_current_font_size)
                plot_font_size.setPlaceholderText("Font size")
                self.elements[element][side]["font_size"] = plot_font_size
                tick_spacing_major = QLineEdit()
                tick_spacing_major.setPlaceholderText("Major ticks")
                self.elements[element][side]["major_ticks"] = tick_spacing_major
                tick_spacing_minor = QLineEdit()
                tick_spacing_minor.setPlaceholderText("Minor ticks")
                self.elements[element][side]["minor_ticks"] = tick_spacing_minor
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
        self.elements["histogram"] = {}

        hist_axis = self.window.plot_elements["histogram"].axis
        box = QGroupBox(self)
        h_layout = QHBoxLayout()
        v_layout = QVBoxLayout()
        plot_axis_text = hist_axis.labelText
        plot_text = QLineEdit(plot_axis_text)
        plot_text.setPlaceholderText("Label")
        self.elements["histogram"]["label"] = plot_text
        plot_current_unit = hist_axis.labelUnits
        plot_unit = QLineEdit(plot_current_unit)
        plot_unit.setPlaceholderText("Unit")
        self.elements["histogram"]["unit"] = plot_unit
        plot_current_font_size = hist_axis.labelStyle["font-size"]
        plot_font_size = QLineEdit(plot_current_font_size)
        plot_font_size.setPlaceholderText("Font size")
        self.elements["histogram"]["font_size"] = plot_font_size
        tick_spacing_major = QLineEdit()
        tick_spacing_major.setPlaceholderText("Major ticks")
        self.elements["histogram"]["major_ticks"] = tick_spacing_major
        tick_spacing_minor = QLineEdit()
        tick_spacing_minor.setPlaceholderText("Minor ticks")
        self.elements["histogram"]["minor_ticks"] = tick_spacing_minor
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

        submit_btn = QPushButton("OK", self)
        submit_btn.clicked.connect(self.data_submitted)
        layout.addWidget(submit_btn)

        self.setLayout(layout)
        self.show()

    def data_submitted(self):
        """
        When data is submited apply changes to graphs in the heatmap window. Grab data from dict and change appearance
        of the heatmap window.

        :return: NoneType
        """

        data = {"main_subplot": {"left": {}, "bottom": {}},
                "line_trace_graph": {"left": {}, "bottom": {}},
                "histogram": {"name": None, "unit": None, "label_style": None, "ticks": None}}

        for element in ["main_subplot", "line_trace_graph"]:
            for side in ('left', 'bottom'):
                data[element][side] = {"name": self.elements[element][side]["label"].text(),
                                       "unit": self.elements[element][side]["unit"].text(),
                                       "label_style": {'font-size': self.elements[element][side]["font_size"].text()},
                                       "ticks": {"minor": self.elements[element][side]["minor_ticks"].text(),
                                                 "major": self.elements[element][side]["major_ticks"].text()}}
        data["histogram"] = {"name": self.elements["histogram"]["label"].text(),
                             "unit": self.elements["histogram"]["unit"].text(),
                             "label_style": {'font-size': self.elements["histogram"]["font_size"].text()},
                             "ticks": {"minor": self.elements["histogram"]["minor_ticks"].text(),
                                       "major": self.elements["histogram"]["major_ticks"].text()}}
                # ax.setLabel(ax.labelText, ax.labelUnits, **label_style)

        self.submitted.emit(data)

    def validate(self):
        pass


class InfoWidget(QWidget):
    def __init__(self, buffer):
        super(InfoWidget, self).__init__()

        self.buffer = buffer
        self.data = {}

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        layout = QGridLayout()
        v_layout = QVBoxLayout()
        dimensions_h_layout = QHBoxLayout()

        dimensions_label = QLabel("Dimensions: ")
        dimensions_h_layout.addWidget(dimensions_label)
        dimensions_line_edit = QLineEdit(str(self.buffer.get_matrix_dimensions()))
        dimensions_line_edit.setDisabled(True)
        dimensions_h_layout.addWidget(dimensions_line_edit)
        v_layout.addLayout(dimensions_h_layout)

        v_layout.addWidget(QLabel("X"))

        x_axis_h_layout = QHBoxLayout()
        x_start_label = QLabel("Start")
        x_start_line_edit = QLineEdit(str(self.buffer.data["x"][0]))
        x_start_line_edit.setDisabled(True)
        x_end_label = QLabel("End")
        x_end_line_edit = QLineEdit(str(self.buffer.data["x"][-1]))
        x_end_line_edit.setDisabled(True)
        x_step_label = QLabel("Step")
        x_step_line_edit = QLineEdit(str((self.buffer.data["x"][-1] - self.buffer.data["x"][0]) / (len(self.buffer.data["x"]) - 1)))
        x_step_line_edit.setDisabled(True)
        x_axis = [x_start_label, x_start_line_edit, x_end_label, x_end_line_edit, x_step_label, x_step_line_edit]
        for e in x_axis:
            x_axis_h_layout.addWidget(e)
        v_layout.addLayout(x_axis_h_layout)

        v_layout.addWidget(QLabel("Y"))

        y_axis_h_layout = QHBoxLayout()
        y_start_label = QLabel("Start")
        y_start_line_edit = QLineEdit(str(self.buffer.data["y"][0]))
        y_start_line_edit.setDisabled(True)
        y_end_label = QLabel("End")
        y_end_line_edit = QLineEdit(str(self.buffer.data["y"][-1]))
        y_end_line_edit.setDisabled(True)
        y_step_label = QLabel("Step")
        y_step_line_edit = QLineEdit(
            str((self.buffer.data["y"][-1] - self.buffer.data["y"][0]) / (len(self.buffer.data["y"]) - 1)))
        y_step_line_edit.setDisabled(True)
        y_axis = [y_start_label, y_start_line_edit, y_end_label, y_end_line_edit, y_step_label, y_step_line_edit]
        for e in y_axis:
            y_axis_h_layout.addWidget(e)
        v_layout.addLayout(y_axis_h_layout)

        layout.addLayout(v_layout, 0, 0)
        self.setLayout(layout)

        self.show()


class InputData(QWidget):

    submitted = pyqtSignal(object)

    def __init__(self, msg):
        super(InputData, self).__init__()

        self.display_msg = msg

        self.init_ui()

    def init_ui(self):
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        v_layout = QVBoxLayout()
        self.explanation_text_label = QLabel(self.display_msg)
        v_layout.addWidget(self.explanation_text_label)
        self.textbox_input_value = QLineEdit("")
        v_layout.addWidget(self.textbox_input_value)
        self.submit_btn = QPushButton("OK")
        self.submit_btn.clicked.connect(self.submit_data)
        v_layout.addWidget(self.submit_btn)

        self.setLayout(v_layout)

        self.show()

    def submit_data(self):

        if is_numeric(self.textbox_input_value.text()):
            self.submitted.emit(self.textbox_input_value.text())
            self.close()
        else:
            show_error_message("Warning", "Input data has to be numeric")


def main():

    app = QApplication(sys.argv)
    """ex = ProgressBarWidget()
    for i in range(0, 100):
        time.sleep(0.05)
        ex.setValue(((i + 1) / 100) * 100)
        QApplication.processEvents()
    ex.close()"""
    ex = InputData("gfsukdfg")
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()