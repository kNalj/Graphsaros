from PyQt5.QtWidgets import QWidget, QDesktopWidget, QHBoxLayout, QApplication, QListWidget, QTabWidget, QVBoxLayout, \
    QScrollArea, QPushButton, QLineEdit, QLabel, QCheckBox, QGroupBox
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon

import sys
from graphs.Heatmap import Heatmap
from data_handlers.QcodesDataBuffer import QcodesData
from helpers import get_location_basename


class SettingsWidget(QWidget):
    """

    """
    submitted = pyqtSignal(object)

    def __init__(self, categories):
        """
        TODO: Documentation

        """
        super(QWidget, self).__init__()

        self.categories = ["General", "Display"]
        if categories is not None:
            for category in categories:
                if category not in self.categories:
                    self.categories.append(category)

        self.option_tabs = {}
        self.tab_widgets = {}

        self.init_ui()

    def init_ui(self):
        """
        TODO: Documentation

        :return:
        """
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 700, 600)

        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon("img/settingsIcon.png"))

        layout = QVBoxLayout()
        self.setLayout(layout)

        h_layout = QHBoxLayout()

        self.categories_list = QListWidget()
        for category in self.categories:
            self.categories_list.addItem(category)
        h_layout.addWidget(self.categories_list)

        self.options_area = QWidget()
        options_area_layout = QVBoxLayout()
        self.options_area.setLayout(options_area_layout)
        h_layout.addWidget(self.options_area, stretch=1)

        layout.addLayout(h_layout)

        h_layout_buttons = QHBoxLayout()

        apply_btn = QPushButton("Apply")
        apply_btn.clicked.connect(self.submit_data)
        h_layout_buttons.addWidget(apply_btn)
        submit_btn = QPushButton("OK")
        submit_btn.clicked.connect(self.submit_and_close)
        h_layout_buttons.addWidget(submit_btn)

        layout.addLayout(h_layout_buttons)

        for category in self.categories:
            self.option_tabs[category] = QTabWidget()
            self.tab_widgets[category] = {}

        self.categories_list.currentItemChanged.connect(self.update_options_area)

        self.show()

    def build_tab(self):
        """
        TODO: Documentation

        :return: QScrollArea that is to be added to the QTabWidget
        """
        # Create scroll area
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        # Create widget that fills scroll area
        scroll_area_widget = QWidget(scroll_area)
        scroll_area.setWidget(scroll_area_widget)

        return scroll_area

    def add_tab(self, category, name, widget):
        """
        TODO: Documentation

        :param category: To which category in the side menu to add this tab to. This category has to already exist in
        side menu.
        :param widget:
        :param name:
        :return: NoneType
        """
        self.tab_widgets[category][name] = widget
        self.option_tabs[category].addTab(widget, name)
        return

    def fill_tab(self, category, name, layout):
        """
        TODO: Documentation

        :param category:
        :param name:
        :param layout:
        :return:
        """
        # set the layout as the layout of the tab
        self.tab_widgets[category][name].setLayout(layout)

    def update_options_area(self, category):
        """

        :param category:
        :return:
        """
        item = self.options_area.layout().itemAt(0)
        if item is not None:
            item.widget().setParent(None)
        self.options_area.layout().addWidget(self.option_tabs[category.text()])

    def submit_data(self):
        """

        :return:
        """
        values = ["test"]
        self.submitted.emit(values)

    def submit_and_close(self):
        """

        :return:
        """
        values = ["test"]
        self.submitted.emit(values)
        self.close()

    def build_general_tabs(self):
        """

        :return:
        """
        raise NotImplementedError

    def build_display_tabs(self):
        """

        :return:
        """
        raise NotImplementedError

    def build_data_tabs(self):
        """

        :return:
        """
        raise NotImplementedError


class HeatMapSettings(SettingsWidget):
    """

    """
    def __init__(self, window: Heatmap):
        """

        :param window:
        """
        # Categories specific for 3d settings widget
        categories = ["General", "Display", "Data"]
        super().__init__(categories)
        self.window = window
        self.extend_ui()

    def extend_ui(self):
        """
        Extend the base user interface with stuff required for heatmap settings

        :return:
        """
        for name, tab in self.build_general_tabs().items():
            scroll = self.build_tab()
            self.add_tab("General", name, scroll)
            self.fill_tab("General", name, tab)
        for name, tab in self.build_display_tabs().items():
            scroll = self.build_tab()
            self.add_tab("Display", name, scroll)
            self.fill_tab("Display", name, tab)
        for name, tab in self.build_data_tabs().items():
            scroll = self.build_tab()
            self.add_tab("Data", name, scroll)
            self.fill_tab("Data", name, tab)

    def build_general_tabs(self):
        """

        :return:
        """
        buffer_tab = self.build_data_buffer_tab()

        return {"Data buffer": buffer_tab}

    def build_display_tabs(self):
        """

        :return:
        """
        main_graph_tab = self.build_main_graph_settings_tab()
        line_trace_tab = self.build_line_trace_graph_settings_tab()
        histogram_tab = self.build_histogram_settings_tab()
        matlab_bar_tab = self.build_matlab_bar_settings_tab()

        return {"Main graph": main_graph_tab, "Line trace graph": line_trace_tab, "Histogram": histogram_tab,
                "Matlab bar": matlab_bar_tab}

    def build_data_tabs(self):
        """

        :return:
        """
        offset_tab = self.build_offset_settings_tab()

        return {"Offset": offset_tab}

    def build_data_buffer_tab(self):
        """

        :return:
        """
        layout = QVBoxLayout()

        location_layout = QHBoxLayout()
        location_label = QLabel("Location of the file: ")
        if self.window is not None:
            location_line_edit = QLineEdit(self.window.data_buffer.location)
        else:
            location_line_edit = QLineEdit("test")
        location_line_edit.setDisabled(True)
        location_layout.addWidget(location_label)
        location_layout.addWidget(location_line_edit)

        name_layout = QHBoxLayout()
        name_label = QLabel("Displayed name: ")
        if self.window is not None:
            name_line_edit = QLineEdit(get_location_basename(self.window.data_buffer.location))
        else:
            name_line_edit = QLineEdit(get_location_basename("test"))
        show_name_label = QLabel("Show name: ")
        show_name_checkbox = QCheckBox()
        name_layout.addWidget(name_label)
        name_layout.addWidget(name_line_edit)
        name_layout.addWidget(show_name_label)
        name_layout.addWidget(show_name_checkbox)

        dimensions_layout = QHBoxLayout()
        dimensions_label = QLabel("Dimensions: ")
        if self.window is not None:
            dimensions_line_edit = QLineEdit(str(self.window.data_buffer.get_matrix_dimensions()))
        else:
            dimensions_line_edit = QLineEdit("[25, 51]")
        dimensions_line_edit.setDisabled(True)
        dimensions_layout.addWidget(dimensions_label)
        dimensions_layout.addWidget(dimensions_line_edit)

        layout.addLayout(location_layout)
        layout.addLayout(name_layout)
        layout.addLayout(dimensions_layout)

        return layout

    def build_main_graph_settings_tab(self):
        """

        :return: QLayout that is to be added to the QTabWidget
        """
        layout = QVBoxLayout()

        plot_label = QLabel("Main graph settings: ")

        v_layout = QVBoxLayout()
        for side in ["Left: ", "Bottom: "]:
            axis = self.window.plot_elements["main_subplot"].getAxis(side[:-2].lower())

            main_group_box = QGroupBox()
            main_group_box.setTitle(side)

            h_layout = QHBoxLayout()
            label_box = QGroupBox()
            label_box.setTitle(side[:-2] + " axis label: ")
            label_box_layout = QVBoxLayout()
            for element in ["Label: ", "Unit: ", "Label font size: "]:
                element_layout = QHBoxLayout()
                label = QLabel(element)
                if element == "Label: ":
                    text = axis.labelText
                elif element == "Unit: ":
                    text = axis.labelUnits
                else:
                    text = axis.labelStyle["font-size"][:-2]
                line_edit = QLineEdit(text)
                element_layout.addWidget(label)
                element_layout.addWidget(line_edit)
                label_box_layout.addLayout(element_layout)

            tick_box = QGroupBox()
            tick_box.setTitle(side[:-2] + " axis ticks: ")
            tick_box_layout = QVBoxLayout()
            for element in ["Major ticks: ", "Minor ticks: ", "Tick font size: "]:
                element_layout = QHBoxLayout()
                label = QLabel(element)
                if element == "Major ticks: ":
                    text = "Major ticks"
                elif element == "Minor ticks: ":
                    text = "Minot ticks"
                else:
                    text = str(axis._pen.width())
                line_edit = QLineEdit(text)
                element_layout.addWidget(label)
                element_layout.addWidget(line_edit)
                tick_box_layout.addLayout(element_layout)

            label_box.setLayout(label_box_layout)
            tick_box.setLayout(tick_box_layout)

            main_group_box.setLayout(h_layout)

            h_layout.addWidget(label_box, stretch=1)
            h_layout.addWidget(tick_box, stretch=1)

            v_layout.addWidget(main_group_box)

        # Add everything to the main layout
        layout.addWidget(plot_label)
        layout.addLayout(v_layout, stretch=1)

        return layout

    def build_line_trace_graph_settings_tab(self):
        """

        :return:
        """
        layout = QVBoxLayout()

        plot_label = QLabel("Line trace graph: ")

        v_layout = QVBoxLayout()
        for side in ["Left: ", "Bottom: ", "Top: "]:
            if side != "Top: ":
                axis = self.window.plot_elements["line_trace_graph"].getAxis(side[:-2].lower())
            else:
                axis = self.window.plot_elements["extra_axis"]

            main_group_box = QGroupBox()
            main_group_box.setTitle(side)

            h_layout = QHBoxLayout()
            label_box = QGroupBox()
            label_box.setTitle(side[:-2] + " axis label: ")
            label_box_layout = QVBoxLayout()

            for element in ["Label: ", "Unit: ", "Label font size: "]:
                element_layout = QHBoxLayout()
                label = QLabel(element)
                if element == "Label: ":
                    text = axis.labelText
                elif element == "Unit: ":
                    text = axis.labelUnits
                else:
                    text = axis.labelStyle["font-size"][:-2]
                line_edit = QLineEdit(text)
                element_layout.addWidget(label)
                element_layout.addWidget(line_edit)
                label_box_layout.addLayout(element_layout)

            tick_box = QGroupBox()
            tick_box.setTitle(side[:-2] + " axis ticks: ")
            tick_box_layout = QVBoxLayout()
            for element in ["Major ticks: ", "Minor ticks: ", "Tick font size: "]:
                element_layout = QHBoxLayout()
                label = QLabel(element)
                if element == "Major ticks: ":
                    text = "Major ticks"
                elif element == "Minor ticks: ":
                    text = "Minot ticks"
                else:
                    text = str(axis._pen.width())
                line_edit = QLineEdit(text)
                element_layout.addWidget(label)
                element_layout.addWidget(line_edit)
                tick_box_layout.addLayout(element_layout)

            label_box.setLayout(label_box_layout)
            tick_box.setLayout(tick_box_layout)

            main_group_box.setLayout(h_layout)

            h_layout.addWidget(label_box, stretch=1)
            h_layout.addWidget(tick_box, stretch=1)

            v_layout.addWidget(main_group_box)

        layout.addWidget(plot_label)
        layout.addLayout(v_layout, stretch=1)

        return layout

    def build_histogram_settings_tab(self):
        """

        :return:
        """
        layout = QVBoxLayout()

        v_layout = QVBoxLayout()
        axis = self.window.plot_elements["histogram"].axis

        main_group_box = QGroupBox()
        main_group_box.setTitle("Histogram: ")

        h_layout = QHBoxLayout()
        label_box = QGroupBox()
        label_box.setTitle("Left: ")
        label_box_layout = QVBoxLayout()

        for element in ["Label: ", "Unit: ", "Label font size: "]:
            element_layout = QHBoxLayout()
            label = QLabel(element)
            if element == "Label: ":
                text = axis.labelText
            elif element == "Unit: ":
                text = axis.labelUnits
            else:
                text = axis.labelStyle["font-size"][:-2]

            line_edit = QLineEdit(text)
            element_layout.addWidget(label)
            element_layout.addWidget(line_edit)
            label_box_layout.addLayout(element_layout)

        label_box.setLayout(label_box_layout)
        main_group_box.setLayout(h_layout)

        h_layout.addWidget(label_box, stretch=1)

        v_layout.addWidget(main_group_box)

        layout.addLayout(v_layout)

        return layout

    def build_matlab_bar_settings_tab(self):
        """

        :return:
        """
        layout = QVBoxLayout()

        v_layout = QVBoxLayout()
        axis = self.window.plot_elements["color_bar"].axis

        h_layout = QHBoxLayout()
        label_box = QGroupBox()
        label_box.setTitle("Left: ")
        label_box_layout = QVBoxLayout()

        main_group_box = QGroupBox()
        main_group_box.setTitle("Matlab bar: ")

        for element in ["Label: ", "Unit: ", "Label font size: "]:
            element_layout = QHBoxLayout()
            label = QLabel(element)
            if element == "Label: ":
                text = axis.labelText
            elif element == "Unit: ":
                text = axis.labelUnits
            else:
                if "font-size" in axis.labelStyle:
                    text = axis.labelStyle["font-size"][:-2]

            line_edit = QLineEdit(text)
            element_layout.addWidget(label)
            element_layout.addWidget(line_edit)
            label_box_layout.addLayout(element_layout)

        label_box.setLayout(label_box_layout)
        main_group_box.setLayout(h_layout)

        h_layout.addWidget(label_box, stretch=1)

        v_layout.addWidget(main_group_box)

        layout.addLayout(v_layout)

        return layout

    def build_offset_settings_tab(self):
        """

        :return:
        """
        layout = QVBoxLayout()

        settings_label = QLabel("Offset settings")

        v_layout = QVBoxLayout()
        for orientation in ["Horizontal", "Vertical"]:
            main_group_box = QGroupBox()
            main_group_box.setTitle(orientation)

            h_layout = QHBoxLayout()
            label = QLabel(orientation + " offset: ")
            line_edit = QLineEdit(str(self.window.offsets[orientation.lower()]))

            h_layout.addWidget(label)
            h_layout.addWidget(line_edit)

            main_group_box.setLayout(h_layout)

            v_layout.addWidget(main_group_box)

        layout.addWidget(settings_label)
        layout.addLayout(v_layout, stretch=1)

        return layout


def main():
    app = QApplication(sys.argv)

    buffer = QcodesData("C:\\Users\\ldrmic\\Projects\\Graphsaros\\other\\QCoDeS_2d1\\IVVI_PLLT_set_IVVI_Ohmic_set.dat")
    buffer.prepare_data()
    hm = Heatmap(buffer)
    ex = HeatMapSettings(hm)

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
