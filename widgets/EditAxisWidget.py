from PyQt5.QtWidgets import QWidget, QDesktopWidget, QGridLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QLineEdit, \
    QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon, QValidator, QIntValidator


class EditAxisWidget(QWidget):
    """
    Base class for widget that displays buffer info

    Buffer info is:
        dimensions: dimensions of the matrix
        x axis: start, end, steps
        y axis: start, end, steps
    """
    submitted = pyqtSignal(object)

    def __init__(self):
        super(EditAxisWidget, self).__init__()

    def init_ui(self):
        """
        Should be implemented in the child classes
        :return:
        """
        raise NotImplementedError

    def data_submitted(self):
        """
        Should be implemented in the child classes
        :return:
        """
        raise NotImplementedError

    def validate(self):
        """
        Should be implemented in the child classes.
        Checks if data submitted is correct.

        :return: boolean: True if data is valid, False if data is not valid
        """
        raise NotImplementedError


class Edit2DAxisWidget(EditAxisWidget):
    def __init__(self, window):
        super(Edit2DAxisWidget, self).__init__()

        self.window = window
        self.elements = {}
        self.validators = {}

        self.init_ui()

    def init_ui(self):
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Edit axis data")
        self.setWindowIcon(QIcon("img/dataStructure.png"))

        layout = QGridLayout()
        validator = QIntValidator()
        self.validators["int"] = validator

        for element in ["main_subplot", "fit_plot"]:
            box = QGroupBox(self)
            h_layout = QHBoxLayout()
            plot_label = QLabel(element.capitalize().replace("_", " "), self)
            layout.addWidget(plot_label)
            self.elements[element] = {}
            self.validators[element] = {}

            for side in ["left", "bottom"]:
                self.elements[element][side] = {}
                v_layout = QVBoxLayout()
                axis = self.window.plot_elements[element].getAxis(side)

                plot_axis_text = axis.labelText
                plot_text = QLineEdit(plot_axis_text)
                plot_text.setPlaceholderText("Label")
                self.elements[element][side]["label"] = plot_text
                plot_current_unit = axis.labelUnits
                plot_unit = QLineEdit(plot_current_unit)
                plot_unit.setPlaceholderText("Unit")
                self.elements[element][side]["unit"] = plot_unit
                plot_current_font_size = axis.labelStyle["font-size"][:-2]
                plot_font_size = QLineEdit(plot_current_font_size)
                plot_font_size.setPlaceholderText("Font size")
                plot_font_size.setValidator(self.validators["int"])
                self.elements[element][side]["font_size"] = plot_font_size
                tick_spacing_major = QLineEdit()
                tick_spacing_major.setPlaceholderText("Major ticks")
                self.elements[element][side]["major_ticks"] = tick_spacing_major
                tick_spacing_minor = QLineEdit()
                tick_spacing_minor.setPlaceholderText("Minor ticks")
                self.elements[element][side]["minor_ticks"] = tick_spacing_minor
                tick_font_size = QLineEdit()
                tick_font_size.setPlaceholderText("Font")
                self.elements[element][side]["tick_font"] = tick_font_size
                self.elements[element][side]["tick_font"].setValidator(self.validators["int"])
                tick_h_layout = QHBoxLayout()
                tick_h_layout.addWidget(tick_spacing_major)
                tick_h_layout.addWidget(tick_spacing_minor)
                tick_h_layout.addWidget(tick_font_size)
                v_layout.addWidget(QLabel(side.capitalize()))
                v_layout.addWidget(plot_text)
                v_layout.addWidget(plot_unit)
                v_layout.addWidget(plot_font_size)
                v_layout.addLayout(tick_h_layout)
                h_layout.addLayout(v_layout)

            box.setLayout(h_layout)
            layout.addWidget(box)

        submit_btn = QPushButton("OK", self)
        submit_btn.clicked.connect(self.data_submitted)
        layout.addWidget(submit_btn)

        self.setLayout(layout)

    def data_submitted(self):
        """

        :return:
        """
        data = {"main_subplot": {"left": {}, "bottom": {}, "top": {}},
                "fit_plot": {"left": {}, "bottom": {}, "top": {}}}

        for element in ["main_subplot", "fit_plot"]:
            for side in ["left", "bottom"]:
                data[element][side] = {"name": self.elements[element][side]["label"].text(),
                                       "unit": self.elements[element][side]["unit"].text(),
                                       "label_style": {
                                           'font-size': self.elements[element][side]["font_size"].text() + "pt"},
                                       "ticks": {"minor": self.elements[element][side]["minor_ticks"].text(),
                                                 "major": self.elements[element][side]["major_ticks"].text(),
                                                 "font": self.elements[element][side]["tick_font"].text()}}

        validation_fail = self.validate()
        if not validation_fail:
            self.submitted.emit(data)
        else:
            self.setFocus(validation_fail)

    def validate(self):
        """

        :return:
        """
        for element in self.elements:
            if element in ["main_subplot", "fit_plot"]:
                for axis in self.elements[element]:
                    for widget in self.elements[element][axis]:
                        if self.elements[element][axis][widget].validator() is not None:
                            validator = self.elements[element][axis][widget].validator()
                            state = validator.validate(self.elements[element][axis][widget].text(), 0)[0]
                            if state == QValidator.Acceptable:
                                return False
                            elif state == QValidator.Intermediate:
                                return False
                            else:
                                return self.elements[element][axis][widget]


class Edit3DAxisWidget(EditAxisWidget):
    def __init__(self, window):
        super(Edit3DAxisWidget, self).__init__()

        # Reference to a window that is being changed
        self.window = window

        self.elements = {}

        self.validators = {}

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Edit axis data")
        self.setWindowIcon(QIcon("img/dataStructure.png"))

        layout = QGridLayout()
        validator = QIntValidator()
        self.validators["int"] = validator

        for element in ["main_subplot", "line_trace_graph"]:
            box = QGroupBox(self)
            h_layout = QHBoxLayout()
            plot_label = QLabel(element.capitalize().replace("_", " "), self)
            layout.addWidget(plot_label)
            self.elements[element] = {}
            self.validators[element] = {}

            if element == "line_trace_graph":
                axes = ["left", "bottom", "top"]
            else:
                axes = ["left", "bottom"]
            for side in axes:
                self.elements[element][side] = {}
                # this one contains all elements of one axis of one plot
                v_layout = QVBoxLayout()
                if side != "top":
                    axis = self.window.plot_elements[element].getAxis(side)
                else:
                    axis = self.window.plot_elements["extra_axis"]

                plot_axis_text = axis.labelText
                plot_text = QLineEdit(plot_axis_text)
                plot_text.setPlaceholderText("Label")
                self.elements[element][side]["label"] = plot_text
                plot_current_unit = axis.labelUnits
                plot_unit = QLineEdit(plot_current_unit)
                plot_unit.setPlaceholderText("Unit")
                self.elements[element][side]["unit"] = plot_unit
                plot_current_font_size = axis.labelStyle["font-size"][:-2]
                plot_font_size = QLineEdit(plot_current_font_size)
                plot_font_size.setPlaceholderText("Font size")
                plot_font_size.setValidator(self.validators["int"])
                self.elements[element][side]["font_size"] = plot_font_size
                tick_spacing_major = QLineEdit()
                tick_spacing_major.setPlaceholderText("Major ticks")
                self.elements[element][side]["major_ticks"] = tick_spacing_major
                tick_spacing_minor = QLineEdit()
                tick_spacing_minor.setPlaceholderText("Minor ticks")
                self.elements[element][side]["minor_ticks"] = tick_spacing_minor
                tick_font_size = QLineEdit()
                tick_font_size.setPlaceholderText("Font")
                self.elements[element][side]["tick_font"] = tick_font_size
                self.elements[element][side]["tick_font"].setValidator(self.validators["int"])
                tick_h_layout = QHBoxLayout()
                tick_h_layout.addWidget(tick_spacing_major)
                tick_h_layout.addWidget(tick_spacing_minor)
                tick_h_layout.addWidget(tick_font_size)
                v_layout.addWidget(QLabel(side.capitalize()))
                v_layout.addWidget(plot_text)
                v_layout.addWidget(plot_unit)
                v_layout.addWidget(plot_font_size)
                v_layout.addLayout(tick_h_layout)
                h_layout.addLayout(v_layout)


            box.setLayout(h_layout)
            layout.addWidget(box)

        plot_label = QLabel("Histogram")
        layout.addWidget(plot_label)
        self.elements["histogram"] = {}

        hist_axis = self.window.plot_elements["histogram"].axis
        box = QGroupBox(self)
        h_layout = QHBoxLayout()
        v_layout = QVBoxLayout()
        plot_axis_text = hist_axis.labelText
        plot_text = QLineEdit(plot_axis_text)
        plot_text.setPlaceholderText("Label")
        self.elements["histogram"]["label"] = plot_text
        plot_current_unit = hist_axis.labelUnits
        plot_unit = QLineEdit(plot_current_unit)
        plot_unit.setPlaceholderText("Unit")
        self.elements["histogram"]["unit"] = plot_unit
        plot_current_font_size = hist_axis.labelStyle["font-size"][:-2]
        plot_font_size = QLineEdit(plot_current_font_size)
        plot_font_size.setPlaceholderText("Font size")
        plot_font_size.setValidator(self.validators["int"])
        self.elements["histogram"]["font_size"] = plot_font_size
        tick_spacing_major = QLineEdit()
        tick_spacing_major.setPlaceholderText("Major ticks")
        self.elements["histogram"]["major_ticks"] = tick_spacing_major
        tick_spacing_minor = QLineEdit()
        tick_spacing_minor.setPlaceholderText("Minor ticks")
        self.elements["histogram"]["minor_ticks"] = tick_spacing_minor
        tick_font_size = QLineEdit()
        tick_font_size.setPlaceholderText("Font")
        self.elements["histogram"]["tick_font"] = tick_font_size
        self.elements["histogram"]["tick_font"].setValidator(self.validators["int"])
        tick_h_layout = QHBoxLayout()
        tick_h_layout.addWidget(tick_spacing_major)
        tick_h_layout.addWidget(tick_spacing_minor)
        tick_h_layout.addWidget(tick_font_size)
        v_layout.addWidget(QLabel("Left"))
        v_layout.addWidget(plot_text)
        v_layout.addWidget(plot_unit)
        v_layout.addWidget(plot_font_size)
        v_layout.addLayout(tick_h_layout)
        h_layout.addLayout(v_layout)
        box.setLayout(h_layout)
        layout.addWidget(box)

        submit_btn = QPushButton("OK", self)
        submit_btn.clicked.connect(self.data_submitted)
        layout.addWidget(submit_btn)

        self.setLayout(layout)
        self.show()

    def data_submitted(self):
        """
        When data is submited apply changes to graphs in the heatmap window. Grab data from dict and change appearance
        of the heatmap window.

        :return: NoneType
        """

        # Main subplot in the heatmap window is the one showing the image of the data
        # left and bottom refers to a location of the axis
        # Line trace graph in the heatmap window is the one showing line traces under lineROI object
        # left, top and bottom refer to axes in that graph
        # Additionally histogram data needs to be stored in a separate dictionary
        data = {"main_subplot": {"left": {}, "bottom": {}},
                "line_trace_graph": {"left": {}, "bottom": {}, "top": {}},
                "histogram": {"name": None, "unit": None, "label_style": None, "ticks": None}}

        for element in ["main_subplot", "line_trace_graph"]:
            if element == "line_trace_graph":
                axes = ["left", "bottom", "top"]
            else:
                axes = ["left", "bottom"]
            for side in axes:
                data[element][side] = {"name": self.elements[element][side]["label"].text(),
                                       "unit": self.elements[element][side]["unit"].text(),
                                       "label_style": {'font-size': self.elements[element][side]["font_size"].text() + "pt"},
                                       "ticks": {"minor": self.elements[element][side]["minor_ticks"].text(),
                                                 "major": self.elements[element][side]["major_ticks"].text(),
                                                 "font": self.elements[element][side]["tick_font"].text()}}
        data["histogram"] = {"name": self.elements["histogram"]["label"].text(),
                             "unit": self.elements["histogram"]["unit"].text(),
                             "label_style": {'font-size': self.elements["histogram"]["font_size"].text() + "pt"},
                             "ticks": {"minor": self.elements["histogram"]["minor_ticks"].text(),
                                       "major": self.elements["histogram"]["major_ticks"].text(),
                                       "font": self.elements["histogram"]["tick_font"].text()}}

        validation_fail = self.validate()
        if not validation_fail:
            self.submitted.emit(data)
        else:
            self.setFocus(validation_fail)

    def validate(self):
        for element in self.elements:
            if element in ["main_subplot", "line_trace_graph"]:
                for axis in self.elements[element]:
                    for widget in self.elements[element][axis]:
                        if self.elements[element][axis][widget].validator() is not None:
                            validator = self.elements[element][axis][widget].validator()
                            state = validator.validate(self.elements[element][axis][widget].text(), 0)[0]
                            if state == QValidator.Acceptable:
                                return False
                            elif state == QValidator.Intermediate:
                                return False
                            else:
                                return self.elements[element][axis][widget]