from pyqtgraph.exporters import Exporter
from pyqtgraph.parametertree import Parameter
from pyqtgraph.GraphicsScene import GraphicsScene
from PyQt5 import QtCore
from PyQt5.QtWidgets import QGraphicsItem
from custom_pg.VideoPlayer import VideoPlayer

__all__ = ['VideoExporter']


class VideoExporter(Exporter):
    Name = "Video file"
    allowCopy = True

    def __init__(self, item):
        Exporter.__init__(self, item)
        tr = self.getTargetRect()
        if isinstance(item, QGraphicsItem):
            scene = item.scene()
        else:
            scene = item
        bgbrush = scene.views()[0].backgroundBrush()
        bg = bgbrush.color()
        if bgbrush.style() == QtCore.Qt.NoBrush:
            bg.setAlpha(0)

        self.item = item

        self.params = Parameter(name='params', type='group', children=[
            {'name': 'width', 'type': 'int', 'value': tr.width(), 'limits': (0, None)},
            {'name': 'height', 'type': 'int', 'value': tr.height(), 'limits': (0, None)},
            {'name': 'antialias', 'type': 'bool', 'value': True},
            {'name': 'background', 'type': 'color', 'value': bg},
        ])
        self.params.param('width').sigValueChanged.connect(self.widthChanged)
        self.params.param('height').sigValueChanged.connect(self.heightChanged)

    def widthChanged(self):
        sr = self.getSourceRect()
        ar = float(sr.height()) / sr.width()
        self.params.param('height').setValue(self.params['width'] * ar, blockSignal=self.heightChanged)

    def heightChanged(self):
        sr = self.getSourceRect()
        ar = float(sr.width()) / sr.height()
        self.params.param('width').setValue(self.params['height'] * ar, blockSignal=self.widthChanged)

    def parameters(self):
        return self.params

    def export(self, fileName=None, toBytes=False, copy=False):
        area = self.getTargetRect()
        point = QtCore.QPoint(area.left(), area.top())
        if isinstance(self.item, GraphicsScene):
            global_point = self.item.parent().mapToGlobal(point)
            w, h = self.params["width"], self.params["height"]
        else:
            global_point = self.item.scene().parent().mapToGlobal(point)
            w, h = self.params["width"] + 10, self.params["height"] + 10

        self.video = VideoPlayer(w, h, global_point)
        self.video.show()


VideoExporter.register()

