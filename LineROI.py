import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QMenu, QAction, QWidgetAction, QSlider


class LineROI(pg.LineSegmentROI):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    # On right-click, raise the context menu
    def mouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.RightButton:
            if self.raiseContextMenu(ev):
                ev.accept()

    def raiseContextMenu(self, ev):
        menu = self.getContextMenus()

        # Let the scene add on to the end of our context menu
        # (this is optional)
        menu = self.scene().addParentContextMenus(self, menu, ev)

        pos = ev.screenPos()
        menu.popup(QtCore.QPoint(pos.x(), pos.y()))
        return True

    # This method will be called when this item's _children_ want to raise
    # a context menu that includes their parents' menus.
    def getContextMenus(self, event=None):
        if self.menu is None:
            self.menu = QMenu()
            self.menu.setTitle("Options")

            # //////////////////////// HORIZONTAL ////////////////////////
            horizontal = QMenu("Set horizontal", self.menu)
            # horizontal.triggered.connect(self.set_horizontal)
            self.menu.horizontal = horizontal
            self.menu.addMenu(horizontal)

            h_line_up_by_point_a = QAction("Point A", horizontal)
            h_line_up_by_point_a.hovered.connect(self.outline)
            h_line_up_by_point_b = QAction("Point B", horizontal)

            horizontal.addAction(h_line_up_by_point_a)
            horizontal.addAction(h_line_up_by_point_b)

            # //////////////////////// VERTICAL ////////////////////////
            vertical = QMenu("Set vertical", self.menu)
            # vertical.triggered.connect(self.set_vertical)
            self.menu.addMenu(vertical)
            self.menu.vertical = vertical

            v_line_up_by_point_a = QAction("Point A", self.menu.vertical)
            v_line_up_by_point_b = QAction("Point B", self.menu.vertical)

            vertical.addAction(v_line_up_by_point_a)
            vertical.addAction(v_line_up_by_point_b)

            angle = QWidgetAction(self.menu)
            angle_slider = QSlider()
            angle_slider.setOrientation(QtCore.Qt.Horizontal)
            angle_slider.setMaximum(360)
            angle_slider.setValue(180)
            angle_slider.valueChanged.connect(self.set_angle)
            angle.setDefaultWidget(angle_slider)
            self.menu.addAction(angle)
            self.menu.angle = angle
            self.angle_slider = angle_slider
            self.menu.alphaSlider = angle_slider
        return self.menu

    def set_horizontal(self):
        pass

    def set_vertical(self):
        pass

    def set_angle(self):
        print(self.angle())
        self.setAngle(self.angle_slider.value())

    def outline(self):
        print("haha")
