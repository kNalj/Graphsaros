from PyQt5.QtWidgets import QWidget, QDesktopWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit


class InfoWidget(QWidget):
    def __init__(self, buffer):
        super(InfoWidget, self).__init__()

        self.buffer = buffer
        self.data = {}

        self.init_ui()

    def init_ui(self):
        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        layout = QGridLayout()
        v_layout = QVBoxLayout()
        dimensions_h_layout = QHBoxLayout()

        dimensions_label = QLabel("Dimensions: ")
        dimensions_h_layout.addWidget(dimensions_label)
        dimensions_line_edit = QLineEdit(str(self.buffer.get_matrix_dimensions()))
        dimensions_line_edit.setDisabled(True)
        dimensions_h_layout.addWidget(dimensions_line_edit)
        v_layout.addLayout(dimensions_h_layout)

        v_layout.addWidget(QLabel("X"))

        x_axis_h_layout = QHBoxLayout()
        x_start_label = QLabel("Start")
        x_start_line_edit = QLineEdit(str(self.buffer.data["x"][0]))
        x_start_line_edit.setDisabled(True)
        x_end_label = QLabel("End")
        x_end_line_edit = QLineEdit(str(self.buffer.data["x"][-1]))
        x_end_line_edit.setDisabled(True)
        x_step_label = QLabel("Step")
        x_step_line_edit = QLineEdit(str((self.buffer.data["x"][-1] - self.buffer.data["x"][0]) / (len(self.buffer.data["x"]) - 1)))
        x_step_line_edit.setDisabled(True)
        x_axis = [x_start_label, x_start_line_edit, x_end_label, x_end_line_edit, x_step_label, x_step_line_edit]
        for e in x_axis:
            x_axis_h_layout.addWidget(e)
        v_layout.addLayout(x_axis_h_layout)

        v_layout.addWidget(QLabel("Y"))

        y_axis_h_layout = QHBoxLayout()
        y_start_label = QLabel("Start")
        y_start_line_edit = QLineEdit(str(self.buffer.data["y"][0][0]))
        y_start_line_edit.setDisabled(True)
        y_end_label = QLabel("End")
        y_end_line_edit = QLineEdit(str(self.buffer.data["y"][0][-1]))
        y_end_line_edit.setDisabled(True)
        y_step_label = QLabel("Step")
        y_step_line_edit = QLineEdit(
            str((self.buffer.data["y"][0][-1] - self.buffer.data["y"][0][0]) / (len(self.buffer.data["y"][0]) - 1)))
        y_step_line_edit.setDisabled(True)
        y_axis = [y_start_label, y_start_line_edit, y_end_label, y_end_line_edit, y_step_label, y_step_line_edit]
        for e in y_axis:
            y_axis_h_layout.addWidget(e)
        v_layout.addLayout(y_axis_h_layout)

        layout.addLayout(v_layout, 0, 0)
        self.setLayout(layout)

        self.show()
