import pyqtgraph as pg
import sys
import numpy as np

from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtGui import QIcon

from BaseGraph import BaseGraph


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class Heatmap(BaseGraph):

    def __init__(self, data=None):
        super().__init__()

        self.setWindowTitle("Heatmap window")
        self.setWindowIcon(QIcon("img/heatmapIcon.png"))
        # need to keep track of number of opened windows and position the newly created one accordingly
        self.plt = pg.GraphicsView()

        self.plt_data = data
        self.active_data = self.plt_data
        self.plt_data_gauss = pg.gaussianFilter(self.plt_data, (1, 4))
        self.display = "normal"

        self.plot_elements = {}

        self.line_segment_roi = {}

        self.init_ui()

    def init_ui(self):

        self.setGeometry(50, 50, 640, 400)
        self.setCentralWidget(self.plt)
        self.show()

        central_item = pg.GraphicsLayout()
        main_subplot = central_item.addPlot()
        img = pg.ImageItem()
        img.setImage(self.plt_data)
        main_subplot.addItem(img)
        for side in ('left', 'bottom'):
            ax = main_subplot.getAxis(side)
            ax.setPen((60, 60, 60))

        iso = pg.IsocurveItem(level=0.8, pen='g')
        iso.setParentItem(img)
        iso.setData(pg.gaussianFilter(self.plt_data, (2, 2)))

        histogram = pg.HistogramLUTItem()
        histogram.setImageItem(img)
        histogram.setFixedWidth(128)

        isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
        histogram.vb.addItem(isoLine)
        histogram.vb.setMouseEnabled(y=False)  # makes user interaction a little easier
        isoLine.setValue(0.8)
        isoLine.setZValue(1000)  # bring iso line above contrast controls
        isoLine.sigDragged.connect(self.update_iso_curve)

        # histogram.axis.setLabel(get_label_from_json_data)
        central_item.addItem(histogram)
        self.plt.setCentralItem(central_item)
        self.plt.setBackground('w')
        central_item.nextRow()
        line_trace_graph = central_item.addPlot(colspan=2, pen=(60, 60, 60))
        line_trace_graph.setMaximumHeight(256)
        for axis in ["left", "bottom"]:
            ax = line_trace_graph.getAxis(axis)
            ax.setPen((60, 60, 60))
        self.plot_elements = {"central_item": central_item, "main_subplot": main_subplot,
                              "img": img, "histogram": histogram, "line_trace_graph": line_trace_graph,
                              "iso": iso, "isoLine": isoLine}

    def init_toolbar(self):

        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)
        self.line_trace_btn = QAction(QIcon("img/lineGraph"), "Line_Trace")
        self.tools.addAction(self.line_trace_btn)
        self.gaussian_filter_btn = QAction(QIcon("img/gaussianIcon.png"), "Gaussian_filter")
        self.tools.addAction(self.gaussian_filter_btn)
        self.exit_action_btn = QAction(QIcon("img/closeIcon.png"), "Exit")
        self.tools.addAction(self.exit_action_btn)

    def line_trace_action(self):
        line_segmet_roi = pg.LineSegmentROI([[5, 5], [22, 22]], pen=(5, 9))
        line_segmet_roi.sigRegionChanged.connect(self.update_line_trace_plot)
        self.line_segment_roi["ROI"] = line_segmet_roi
        self.plot_elements["main_subplot"].addItem(line_segmet_roi)

    def update_line_trace_plot(self):
        data = self.active_data
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        line_trace_graph = self.plot_elements["line_trace_graph"]
        line_trace_graph.plot(selected, pen=(60, 60, 60), clear=True)

    def gaussian_filter_action(self):
        if self.display != "gauss":
            self.plot_elements["img"].setImage(self.plt_data_gauss)
            self.active_data = self.plt_data_gauss
            self.display = "gauss"
        else:
            self.plot_elements["img"].setImage(self.plt_data)
            self.display = "normal"
            self.active_data = self.plt_data

    def lorentzian_filter_action(self):
        pass

    def update_iso_curve(self):
        self.plot_elements["iso"].setLevel(self.plot_elements["isoLine"].value())


def main():

    app = QApplication(sys.argv)
    data = np.random.normal(size=(200, 100))
    data1 = np.zeros((200, 100))
    for index, i in enumerate(data1):
        new = np.linspace(0, 10*np.pi, 100)
        # print(np.sin(new))
        i += 10*np.exp(-index/50)*np.sin(new)
    ex = Heatmap(data=data1)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()