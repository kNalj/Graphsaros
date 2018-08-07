from PyQt5.QtWidgets import QWidget, QApplication, QDesktopWidget, QGridLayout, QCheckBox, QVBoxLayout, QLabel, \
    QScrollArea, QPushButton, QHBoxLayout
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal

from data_handlers.QcodesDataBuffer import QcodesData
from data_handlers.QtLabDataBuffer import QtLabData
from data_handlers.MatrixFileDataBuffer import MatrixData

import pyqtgraph as pg

import sys
import os


class BufferExplorer(QWidget):

    submitted = pyqtSignal(object)
    add_requested = pyqtSignal(object)

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
        self.setGeometry(int(0.2 * width), int(0.2 * height), 800, 600)

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
                    histogram = pg.HistogramLUTItem()
                    histogram.setImageItem(img)
                    histogram.gradient.loadPreset("thermal")
                    main_subplot.addItem(img)

                v_layout = QVBoxLayout()
                v_layout.addWidget(QLabel(os.path.basename(candidate)[:30]))
                h_layout = QHBoxLayout()
                checkbox = QCheckBox(self)
                what_btn = QPushButton("What is this", self)
                what_btn.clicked.connect(self.make_go_to_location(self.buffers[candidate]))
                add_btn = QPushButton("Quick add", self)
                add_btn.clicked.connect(self.make_quick_add(candidate))
                self.checkboxes[candidate] = checkbox
                h_layout.addWidget(checkbox)
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
        candidates = []
        for root, dirs, files in os.walk(self.root_folder):
            for file in files:
                if file.endswith(".dat"):
                    file = os.path.join(root, file)
                    candidates.append(file)
        return candidates

    def submit(self):
        selected = {}
        for candidate, checkbox in self.checkboxes.items():
            if checkbox.checkState():
                selected[candidate] = self.buffers[candidate]

        self.submitted.emit(selected)

    def make_quick_add(self, candidate):
        def quick_add():
            self.add_requested.emit({candidate: self.buffers[candidate]})
        return quick_add

    def make_go_to_location(self, buffer):
        def go_to_location():
            location = buffer.get_location()
            folder = os.path.dirname(location)
            # unfortunately this thing only works on windows :((((
            os.startfile(folder)
        return go_to_location

def main():
    app = QApplication(sys.argv)
    ex = BufferExplorer("")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()