from PyQt5.QtWidgets import QWidget, QApplication, QDesktopWidget, QGridLayout, QCheckBox, QVBoxLayout, QLabel, \
    QScrollArea, QPushButton, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

from data_handlers.QcodesDataBuffer import QcodesData
from data_handlers.QtLabDataBuffer import QtLabData
from data_handlers.MatrixFileDataBuffer import MatrixData
from helpers import InfoWidget

import pyqtgraph as pg

import sys
import os


class BufferExplorer(QWidget):

    submitted = pyqtSignal(object)
    add_requested = pyqtSignal(object)

    """
    Buffer explorer is a widget that accepts a string representation of a floder on a file system and walks through that
    folder finding all .dat files within it and its subfolders (recursively) and adds mini graph representation of them
    to self along some additional data about them.
    
    It is used to quickly browse through a large set of datasets and gives you an
    """

    def __init__(self, folder):
        super(BufferExplorer, self).__init__()

        self.root_folder = folder
        self.candidates = self.find_candidate_files()
        self.buffers = {}
        self.checkboxes = {}

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 900, 600)

        self.setWindowTitle("Browse files")
        self.setWindowIcon(QIcon("img/dataStructure.png"))

        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        scroll_content = QWidget(self.scroll)

        main_layout = QGridLayout(self)
        main_layout.addWidget(self.scroll)

        layout = QGridLayout()
        row, column = 0, 0

        for candidate in self.candidates:
            with open(candidate, "r") as current_file:
                for i, line in enumerate(current_file):
                    if i == 2:
                        if line.strip(" \n") == "":
                            self.buffers[candidate] = QtLabData(candidate)
                        elif line.startswith("#"):
                            self.buffers[candidate] = QcodesData(candidate)
                        else:
                            self.buffers[candidate] = MatrixData(candidate)

                        break

            if self.buffers[candidate].is_data_ready():
                mini_plot_widget = QWidget(self)
                mini_plot_widget.setMinimumHeight(250)

                preview_plt = pg.GraphicsView()
                mini_plot = pg.GraphicsLayout()
                main_subplot = mini_plot.addPlot()
                for axis in ["left", "bottom"]:
                    ax = main_subplot.getAxis(axis)
                    ax.setPen((60, 60, 60))

                preview_plt.setCentralItem(mini_plot)
                preview_plt.setBackground('w')

                if self.buffers[candidate].get_number_of_dimension() == 2:
                    main_subplot.clear()
                    main_subplot.plot(x=self.buffers[candidate].get_x_axis_values(),
                                      y=self.buffers[candidate].get_y_axis_values(),
                                      pen=(60, 60, 60))
                else:
                    main_subplot.clear()
                    img = pg.ImageItem()
                    img.setImage(self.buffers[candidate].get_matrix())
                    (x_scale, y_scale) = self.buffers[candidate].get_scale()
                    img.translate(self.buffers[candidate].get_x_axis_values()[0],
                                  self.buffers[candidate].get_y_axis_values()[0])
                    img.scale(x_scale, y_scale)
                    histogram = pg.HistogramLUTItem()
                    histogram.setImageItem(img)
                    histogram.gradient.loadPreset("thermal")
                    main_subplot.addItem(img)
                    legend = {"left": "y", "bottom": "x"}
                    for side in ('left', 'bottom'):
                        ax = main_subplot.getAxis(side)
                        ax.setPen((60, 60, 60))
                        axis_data = self.buffers[candidate].axis_values[legend[side]]
                        label_style = {'font-size': '7pt'}
                        ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

                v_layout = QVBoxLayout()
                v_layout.addWidget(QLabel(os.path.basename(candidate)[:30]))
                h_layout = QHBoxLayout()
                checkbox = QCheckBox(self)
                info_btn = QPushButton("Info", self)
                info_btn.clicked.connect(self.make_show_buffer_info(self.buffers[candidate]))
                what_btn = QPushButton("What is this", self)
                what_btn.clicked.connect(self.make_go_to_location(self.buffers[candidate]))
                add_btn = QPushButton("Quick add", self)
                add_btn.clicked.connect(self.make_quick_add(candidate))
                self.checkboxes[candidate] = checkbox
                h_layout.addWidget(checkbox)
                h_layout.addWidget(info_btn)
                h_layout.addWidget(what_btn)
                h_layout.addWidget(add_btn)
                v_layout.addLayout(h_layout)
                v_layout.addWidget(preview_plt)
                mini_plot_widget.setLayout(v_layout)
                layout.addWidget(mini_plot_widget, row, column, 1, 1)

                if column == 2:
                    row += 1
                    column = 0
                else:
                    column += 1

        submit_btn = QPushButton("OK", self)
        submit_btn.clicked.connect(self.submit)
        main_layout.addWidget(submit_btn, row+1, 0, 1, 3)
        scroll_content.setLayout(layout)
        self.scroll.setWidget(scroll_content)
        self.setLayout(main_layout)

        self.show()

    def find_candidate_files(self):
        """
        Walks throught the folder and its subfolders and returns a list of all files that have extension .dat

        :return:
        """
        candidates = []
        for root, dirs, files in os.walk(self.root_folder):
            for file in files:
                if file.endswith(".dat"):
                    file = os.path.join(root, file)
                    candidates.append(file)
        return candidates

    def submit(self):
        """
        Prepare data for signal to be sent to the main window. Create a dict with locations as keys and buffers as
        values. and emit a signal with that dictionary as data.

        :return:
        """
        selected = {}
        for candidate, checkbox in self.checkboxes.items():
            if checkbox.checkState():
                selected[candidate] = self.buffers[candidate]

        self.submitted.emit(selected)

    def make_quick_add(self, candidate):
        """
        Function factory:
        Quickly add one buffer to the main window . Method is called when a button above the buffers mini graph is
        clicked

        :param candidate: string:
        :return: pointer to a function that emits a signal to add a single buffer to the main window
        """
        def quick_add():
            self.add_requested.emit({candidate: self.buffers[candidate]})
        return quick_add

    def make_go_to_location(self, buffer):
        """
        Function factory:
        Makes functions that open a file explorer to a location where the buffer was taken from (parrent directory)

        :param buffer: DataBuffer: a reference to one of the data buffers displayed in the window
        :return:
        """
        def go_to_location():
            location = buffer.get_location()
            folder = os.path.dirname(location)
            # unfortunately this thing only works on windows :((((
            os.startfile(folder)
        return go_to_location

    def make_show_buffer_info(self, buffer):
        """
        Function factory
        Creates a function that opens a InfoWidget widget for a specific buffer displayed in this window

        :param buffer: reference to one of the buffers in this widget
        :return: pointer to a function that opens a new InfoWidget
        """
        def show_buffer_info():
            self.iw = InfoWidget(buffer)
            self.iw.show()
        return show_buffer_info


def main():
    app = QApplication(sys.argv)
    ex = BufferExplorer("")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()