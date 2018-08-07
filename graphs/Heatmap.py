import pyqtgraph as pg
import sys

from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtGui import QIcon

from graphs.BaseGraph import BaseGraph
from data_handlers.DataBuffer import DataBuffer
from data_handlers.QtLabDataBuffer import QtLabData
from LineROI import LineROI


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class Heatmap(BaseGraph):

    def __init__(self, data: DataBuffer):
        super().__init__()

        # setting the window title, i would have never guessed its this
        self.setWindowTitle("Heatmap window")

        # khm khm ... setting window icon ...
        self.setWindowIcon(QIcon("../img/heatmapIcon.png"))

        # set status bar msg to nothing, just to have it there, later its used to show coordinates of mouse
        self.statusBar().showMessage("")

        # need to keep track of number of opened windows and position the newly created one accordingly
        self.plt = pg.GraphicsView()

        # inastance of DataBuffer class, holds all data required to draw a graph
        self.data_buffer = data

        # np.array, this is what pyqtgraph wants to draw stuff
        self.plt_data = self.data_buffer.get_matrix()

        # to be able to switch between gauss, lorentz, normal, ...
        self.active_data = self.plt_data

        # gauss data
        self.plt_data_gauss = pg.gaussianFilter(self.plt_data, (2, 2))

        # indicates currently displayed data
        self.display = "normal"

        # references to all widgets in this window
        self.plot_elements = {}

        # reference to ROI
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
            label_style = {'font-size': '10pt'}
            ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

        iso = pg.IsocurveItem(level=0.8, pen='g')
        iso.setParentItem(img)
        iso.setData(pg.gaussianFilter(self.plt_data, (2, 2)))

        histogram = pg.HistogramLUTItem()
        histogram.setImageItem(img)
        histogram.gradient.loadPreset("thermal")
        histogram.setFixedWidth(128)
        axis_data = self.data_buffer.axis_values["z"]
        histogram.axis.setLabel(axis_data["name"], axis_data["unit"])

        isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
        histogram.vb.addItem(isoLine)
        histogram.vb.setMouseEnabled(y=False)  # makes user interaction a little easier
        isoLine.setValue(self.plt_data.mean())
        isoLine.setZValue(1000)  # bring iso line above contrast controls
        isoLine.sigDragged.connect(self.update_iso_curve)

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

        main_subplot.scene().sigMouseMoved.connect(self.mouse_moved)

    def init_toolbar(self):
        """
        Create toolbar and add actions to it

        :return: NoneType
        """

        self.tools = self.addToolBar("Tools")
        self.tools.actionTriggered[QAction].connect(self.perform_action)
        self.line_trace_btn = QAction(QIcon("../img/lineGraph"), "Line_Trace", self)
        self.tools.addAction(self.line_trace_btn)
        self.gaussian_filter_btn = QAction(QIcon("../img/gaussianIcon.png"), "Gaussian_filter", self)
        self.tools.addAction(self.gaussian_filter_btn)
        self.exit_action_btn = QAction(QIcon("../img/closeIcon.png"), "Exit", self)
        self.tools.addAction(self.exit_action_btn)
        self.customize_font_btn = QAction(QIcon("../img/editFontIcon.png"), "Font", self)
        self.tools.addAction(self.customize_font_btn)

    def line_trace_action(self):
        """
        Add a line segment region of interest (ROI) to the main subplot. Connect it to a function that updates line
        trace graph anytime one of the handles or the ROI itself is moved.

        :return:
        """
        # ROI instantiation
        line_segmet_roi = LineROI(positions=([self.data_buffer.get_x_axis_values()[0],
                                              self.data_buffer.get_y_axis_values()[0]],
                                             [self.data_buffer.get_x_axis_values()[-1],
                                              self.data_buffer.get_y_axis_values()[0]]),
                                  pos=(0, 0),
                                  pen=(5, 9),
                                  # maxBounds=QRectF(self.data_buffer.get_x_axis_values()[0],
                                  #                  self.data_buffer.get_y_axis_values()[0],
                                  #                  self.data_buffer.get_x_axis_values()[-1],
                                  #                  self.data_buffer.get_y_axis_values()[-1]),
                                  edges=[self.data_buffer.get_x_axis_values()[0],
                                         self.data_buffer.get_x_axis_values()[-1],
                                         self.data_buffer.get_y_axis_values()[0],
                                         self.data_buffer.get_y_axis_values()[-1]])
        # connect signal to a slot
        line_segmet_roi.sigRegionChanged.connect(self.update_line_trace_plot)
        # make a reference to this ROI so i can use it later
        self.line_segment_roi["ROI"] = line_segmet_roi
        # add the ROI to main subplot
        self.plot_elements["main_subplot"].addItem(line_segmet_roi)
        # connect signal to a slot, this signa
        line_segmet_roi.aligned.connect(self.update_line_trace_plot)

    def font_action(self):
        for side in ('left', 'bottom'):
            ax = self.plot_elements["main_subplot"].getAxis(side)
            label_style = {'font-size': '18pt'}
            ax.setLabel(ax.labelText, ax.labelUnits, **label_style)



    def update_line_trace_plot(self):
        data = self.active_data
        img = self.plot_elements["img"]
        selected = self.line_segment_roi["ROI"].getArrayRegion(data, img)
        line_trace_graph = self.plot_elements["line_trace_graph"]
        new_plot = line_trace_graph.plot(selected, pen=(60, 60, 60), clear=True)
        point = self.line_segment_roi["ROI"].getSceneHandlePositions(0)
        _, scene_coords = point
        coords = self.line_segment_roi["ROI"].mapSceneToParent(scene_coords)
        new_plot.translate(coords.x(), 0)
        scale_x, scale_y = self.data_buffer.get_scale()
        new_plot.scale(scale_x, 1)

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
            string = "[Position: {}, {}]".format(int(mouse_point.x()), int(mouse_point.y()))
            self.statusBar().showMessage(string)


def main():

    app = QApplication(sys.argv)

    # Daniels 3D measurement example in QCoDeS
    file_location = "K:\\Measurement\\Daniel\\2017-07-04\\#117_Belle_3to6_Daimond_PLLT_LTon700_CTon910_SLon1900_17-13-25\\IVVI_PLLT_set_IVVI_Ohmic_set.dat"

    # Josip 3D measurement example in QtLab
    file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat"

    # Josips 3D measurement example matrix file
    # file_location = "C:\\Users\\ldrmic\\Downloads\\113622_1_3 IV 560.dat_matrix"

    # Matthias huge ass file
    # file_location = "C:\\Users\\ldrmic\\Documents\\GitHub\\Graphsaros\\other\\005802_GatevsGate_W3_1I03_NW-l_g3@2060_g5@2260_BZ_0T_-_3T_time.dat"

    data = QtLabData(file_location)
    # data = MatrixData(file_location)

    ex = Heatmap(data=data)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
