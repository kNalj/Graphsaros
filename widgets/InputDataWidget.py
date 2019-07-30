from PyQt5.QtWidgets import QWidget, QDesktopWidget, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from helpers import show_error_message, is_numeric


class InputData(QWidget):

    submitted = pyqtSignal(object)

    def __init__(self, msg, num_of_fields, default_value=None, numeric=False, placeholders=None,
                 dropdown=False, dropdown_text=None, dropdown_options=None):
        super(InputData, self).__init__()

        self.display_msg = msg

        self.number_of_input_fields = num_of_fields

        self.numeric = numeric

        if default_value is not None:
            self.default = default_value
        else:
            self.default = []
            for i in range(num_of_fields):
                self.default.append("")

        if placeholders is not None:
            self.placeholders = placeholders
        else:
            self.placeholders = []
            for i in range(num_of_fields):
                self.placeholders.append("Unspecified field")

        if dropdown:
            self.dropdown = True
            self.dropdown_text = dropdown_text
            self.dropdown_options = dropdown_options
        else:
            self.dropdown = False

        self.textboxes = []

        self.init_ui()

    def init_ui(self):
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Ola senor !")
        self.setWindowIcon(QIcon("img/question_mark_icon.png"))

        v_layout = QVBoxLayout()
        self.explanation_text_label = QLabel(self.display_msg)
        v_layout.addWidget(self.explanation_text_label)

        if self.dropdown:
            v_layout.addWidget(QLabel(self.dropdown_text))
            self.combobox = QComboBox()
            for name, data in self.dropdown_options.items():
                self.combobox.addItem(name, data)
            v_layout.addWidget(self.combobox)

        for i in range(self.number_of_input_fields):
            textbox = QLineEdit(self.default[i])
            textbox.setPlaceholderText(self.placeholders[i])
            self.textboxes.append(textbox)
            v_layout.addWidget(textbox)
        # self.textbox_input_value = QLineEdit(self.default)
        # v_layout.addWidget(self.textbox_input_value)
        self.submit_btn = QPushButton("OK")
        self.submit_btn.clicked.connect(self.submit_data)
        v_layout.addWidget(self.submit_btn)

        self.setLayout(v_layout)

        self.show()

    def submit_data(self):

        send_value = []
        for i, numeric_required in enumerate(self.numeric):
            if numeric_required:
                if is_numeric(self.textboxes[i].text()):
                    send_value.append(self.textboxes[i].text())
                else:
                    show_error_message("Warning", "Input data has to be numeric")
                    return
            else:
                send_value.append(self.textboxes[i].text())

        if self.dropdown:
            send_value.append(self.combobox.currentData())

        self.submitted.emit(send_value)
        self.close()
