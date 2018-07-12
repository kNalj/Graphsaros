import pyqtgraph as pg
import sys
import numpy as np

from PyQt5.QtWidgets import QAction, QApplication, QLabel, QSizePolicy
from PyQt5.QtGui import QIcon

from BaseGraph import BaseGraph
from data_handlers.QcodesDataBuffer import QcodesData, DataBuffer


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class Heatmap(BaseGraph):

    def __init__(self, data: DataBuffer):
        super().__init__()

        self.setWindowTitle("Heatmap window")
        self.setWindowIcon(QIcon("img/heatmapIcon.png"))
        # need to keep track of number of opened windows and position the newly created one accordingly
        self.plt = pg.GraphicsView()

        self.data_buffer = data
        self.plt_data = self.data_buffer.get_matrix()
        self.active_data = self.plt_data
        self.plt_data_gauss = pg.gaussianFilter(self.plt_data, (2, 2))
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
        img.translate(self.data_buffer.get_x_axis_values()[0], self.data_buffer.get_y_axis_values()[0])
        (x_scale, y_scale) = self.data_buffer.get_scale()
        img.scale(x_scale, y_scale)
        main_subplot.addItem(img)
        legend = {"left": "y", "bottom": "x"}
        for side in ('left', 'bottom'):
            ax = main_subplot.getAxis(side)
            ax.setPen((60, 60, 60))
            axis_data = self.data_buffer.axis_values[legend[side]]
            labelStyle = {'font-size': '10pt'}
            ax.setLabel(axis_data["name"], axis_data["unit"], **labelStyle)

        iso = pg.IsocurveItem(level=0.8, pen='g')
        iso.setParentItem(img)
        iso.setData(pg.gaussianFilter(self.plt_data, (2, 2)))

        histogram = pg.HistogramLUTItem()
        histogram.setImageItem(img)
        histogram.setFixedWidth(128)
        axis_data = self.data_buffer.axis_values["z"]
        histogram.axis.setLabel(axis_data["name"], axis_data["unit"])

        isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
        histogram.vb.addItem(isoLine)
        histogram.vb.setMouseEnabled(y=False)  # makes user interaction a little easier
        isoLine.setValue(self.plt_data.mean())
        isoLine.setZValue(1000)  # bring iso line above contrast controls
        isoLine.sigDragged.connect(self.update_iso_curve)

        # histogram.axis.setLabel(get_label_from_json_data)
        central_item.addItem(histogram)
        self.plt.setCentralItem(central_item)
        self.plt.setBackground('w')
        central_item.nextRow()
        line_trace_graph = central_item.addPlot(colspan=2, pen=(60, 60, 60))
        line_trace_graph.setMaximumHeight(256)
        legend = {"left": "z", "bottom": "x"}
        for axis in ["left", "bottom"]:
            ax = line_trace_graph.getAxis(axis)
            ax.setPen((60, 60, 60))
            axis_data = self.data_buffer.axis_values[legend[axis]]
            ax.setLabel(axis_data["name"], axis_data["unit"])
        self.plot_elements = {"central_item": central_item, "main_subplot": main_subplot,
                              "img": img, "histogram": histogram, "line_trace_graph": line_trace_graph,
                              "iso": iso, "isoLine": isoLine}

        # proxy = pg.SignalProxy(main_subplot.scene().sigMouseMoved, rateLimit=60, slot=self.mouse_moved)
        main_subplot.scene().sigMouseMoved.connect(self.mouse_moved)

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
        line_segmet_roi = pg.LineSegmentROI([[self.data_buffer.get_x_axis_values()[0],
                                              self.data_buffer.get_y_axis_values()[0]],
                                             [self.data_buffer.get_x_axis_values()[-1],
                                              self.data_buffer.get_y_axis_values()[-1]]],
                                            pen=(5, 9))
        line_segmet_roi.sigRegionChanged.connect(self.update_line_trace_plot)
        self.line_segment_roi["ROI"] = line_segmet_roi
        self.plot_elements["main_subplot"].addItem(line_segmet_roi)

    def update_line_trace_plot(self):
        data = self.active_data
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        line_trace_graph = self.plot_elements["line_trace_graph"]
        line_trace_graph.plot(selected, pen=(60, 60, 60), clear=True)
        # line_trace_graph.plot(selected, pen=(60, 60, 60), clear=True, symbol="o")

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

    def mouse_moved(self, evt):
        pos = evt
        if self.plot_elements["main_subplot"].sceneBoundingRect().contains(pos):
            mouse_point = self.plot_elements["main_subplot"].vb.mapSceneToView(pos)
            index_x = int(mouse_point.x())
            index_y = int(mouse_point.y())
            if index_x and index_x < len(self.data_buffer.get_x_axis_values()) and \
                    index_y and index_y < len(self.data_buffer.get_y_axis_values()):
                self.label.setText()

            string = str(int(mouse_point.x())) + ", " + str(int(mouse_point.y()))
            self.statusBar().showMessage(string)


def main():

    app = QApplication(sys.argv)

    # Daniels 3D measurement example
    file_location = "K:\\Measurement\\Daniel\\2017-07-04\\#117_Belle_3to6_Daimond_PLLT_LTon700_CTon910_SLon1900_17-13-25\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"
    data = QcodesData(file_location)
    ex = Heatmap(data=data)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
