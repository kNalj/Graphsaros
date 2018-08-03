from PyQt5.QtWidgets import QWidget, QApplication, QDesktopWidget, QGridLayout, QCheckBox, QVBoxLayout, QLabel, \
    QScrollArea, QPushButton
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

    def __init__(self, folder):
        super(BufferExplorer, self).__init__()

        self.root_folder = folder
        self.candidates = self.find_candidate_files()
        self.buffers = {}
        self.checkboxes = {}

        """self.scroll = QScrollArea()
        self.scroll.setWidget(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setMaximumSize(1200, 800)"""

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 600, 400)

        self.setWindowTitle("Browse files")
        self.setWindowIcon(QIcon("img/dataStructure.png"))

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
                                      y=self.buffers[candidate].get_y_axis_values())
                else:
                    main_subplot.clear()
                    img = pg.ImageItem()
                    img.setImage(self.buffers[candidate].get_matrix())
                    main_subplot.addItem(img)

                v_layout = QVBoxLayout()
                v_layout.addWidget(QLabel(os.path.basename(candidate)[:30]))
                checkbox = QCheckBox(self)
                self.checkboxes[candidate] = checkbox
                v_layout.addWidget(checkbox)
                v_layout.addWidget(preview_plt)

                layout.addLayout(v_layout, row, column, 1, 1)

                if column == 2:
                    row += 1
                    column = 0
                else:
                    column += 1

        submit_btn = QPushButton("OK", self)
        submit_btn.clicked.connect(self.submit)
        layout.addWidget(submit_btn, row+1, 0, 1, 3)
        self.setLayout(layout)

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

def main():
    app = QApplication(sys.argv)
    ex = BufferExplorer("")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()