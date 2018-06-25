import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, qApp, QToolBar, QWidget, QMainWindow, QApplication, QGridLayout
from PyQt5.QtGui import QIcon

from BaseGraph import BaseGraph


class Heatmap(BaseGraph):

    def __init__(self, data):
        super().__init__()

        self.setWindowTitle("Heatmap window")
        self.setWindowIcon(QIcon("img/heatmapIcon.png"))
        # need to keep track of number of opened windows and position the newly created one accordingly
        self.plt = pg.GraphicsView()
        central_item = pg.GraphicsLayout()
        main_subplot = central_item.addPlot()
        img = pg.ImageItem()
        main_subplot.addItem(img)
        for side in ('left', 'bottom'):
            ax = main_subplot.getAxis(side)
            ax.setPen((60, 60, 60))
        histogram = pg.HistogramLUTItem()
        histogram.setImageItem(img)
        histogram.setFixedWidth(100)
        # histogram.axis.setLabel(get_label_from_json_data)
        central_item.addItem(histogram)
        self.plt.setCentralItem(central_item)
        self.plt.setBackground('w')
        central_item.nextRow()
        p2 = central_item.addPlot(colspan=2, pen=(60, 60, 60))
        p2.setMaximumHeight(150)
        self.init_ui()

    def init_ui(self):

        self.setGeometry(50, 50, 640, 400)
        self.setCentralWidget(self.plt)
        self.show()

    def init_toolbar(self):

        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)
        self.exit_action_Btn = QAction(QIcon("img/closeIcon.png"), "Exit")
        self.tools.addAction(self.exit_action_Btn)


def main():
    app = QApplication(sys.argv)
    ex = Heatmap([])
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()