import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QMenu, QAction, QWidgetAction, QSlider

from helpers import show_error_message


class LineROI(pg.LineSegmentROI):
    aligned = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.temp_line = 0

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
            self.menu.horizontal = horizontal
            self.menu.addMenu(horizontal)

            h_line_up_by_point_a = QAction("Point A", horizontal)
            h_line_up_by_point_a.hovered.connect(lambda: self.hover_action(0, "horizontal"))
            h_line_up_by_point_a.triggered.connect(lambda: self.align_line_trace_ROI(0, "horizontal"))
            h_line_up_by_point_b = QAction("Point B", horizontal)
            h_line_up_by_point_b.hovered.connect(lambda: self.hover_action(1, "horizontal"))
            h_line_up_by_point_b.triggered.connect(lambda: self.align_line_trace_ROI(1, "horizontal"))

            horizontal.addAction(h_line_up_by_point_a)
            horizontal.addAction(h_line_up_by_point_b)

            # //////////////////////// VERTICAL ////////////////////////
            vertical = QMenu("Set vertical", self.menu)
            # vertical.triggered.connect(self.set_vertical)
            self.menu.addMenu(vertical)
            self.menu.vertical = vertical

            v_line_up_by_point_a = QAction("Point A", self.menu.vertical)
            v_line_up_by_point_a.hovered.connect(lambda: self.hover_action(0, "vertical"))
            v_line_up_by_point_a.triggered.connect(lambda: self.align_line_trace_ROI(0, "vertical"))
            v_line_up_by_point_b = QAction("Point B", self.menu.vertical)
            v_line_up_by_point_b.hovered.connect(lambda: self.hover_action(1, "vertical"))
            v_line_up_by_point_b.triggered.connect(lambda: self.align_line_trace_ROI(1, "vertical"))

            vertical.addAction(v_line_up_by_point_a)
            vertical.addAction(v_line_up_by_point_b)

            # //////////////////////// SLIDER ////////////////////////
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

            self.menu.closeEvent = self.leave_menu_event
        return self.menu

    def leave_menu_event(self, event):
        if self.temp_line:
            self.parentItem().scene().removeItem(self.temp_line)
            self.temp_line = 0

    def hover_action(self, point: int, orientation: str):
        point = self.getSceneHandlePositions()[point]
        name, scene_coords = point
        coords = self.mapSceneToParent(scene_coords)

        if orientation == "horizontal":
            self.add_preview(coords.y(), orientation)
        elif orientation == "vertical":
            self.add_preview(coords.x(), orientation)
        else:
            show_error_message("Warning", "Non existent orientation. HOW THE HELL DID U MANAGE TO DO THIS !?")
            return

    def add_preview(self, position, orientation):
        pen = pg.mkPen('y', width=1, style=QtCore.Qt.DashLine)
        if orientation == "vertical":
            new_line = pg.InfiniteLine(angle=90, pen=pen, movable=False)
            new_line.setPos(position)
        elif orientation == "horizontal":
            new_line = pg.InfiniteLine(angle=0, pen=pen, movable=False)
            new_line.setPos(position)

        if not self.temp_line:
            self.temp_line = new_line
            self.parentItem().addItem(self.temp_line)
        else:
            if not (self.temp_line.pos() == new_line.pos() and self.temp_line.angle == new_line.angle):
                self.parentItem().scene().removeItem(self.temp_line)
                self.temp_line = new_line
                self.parentItem().addItem(self.temp_line)

    def align_line_trace_ROI(self, point, orientation):
        handle_to_be_moved = self.getHandles()[1-point]
        align_to_this_point = self.getSceneHandlePositions(point)
        _, align_scene_coords = align_to_this_point
        align_coords = self.mapSceneToParent(align_scene_coords)
        move_this_point = self.getSceneHandlePositions(1-point)
        _, move_scene_coords = move_this_point
        move_coords = self.mapSceneToParent(move_scene_coords)
        if orientation == "horizontal":
            self.movePoint(handle_to_be_moved, (move_coords.x(), align_coords.y()))
        elif orientation == "vertical":
            self.movePoint(handle_to_be_moved, (align_coords.x(), move_coords.y()))

        self.align_points()

    def set_angle(self):
        print(self.angle())
        self.setAngle(self.angle_slider.value())

    def align_points(self):
        self.aligned.emit()

