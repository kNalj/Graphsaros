from PyQt5.QtWidgets import QWidget, QDesktopWidget, QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QLineEdit, \
    QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from helpers import show_error_message, is_numeric


class DiDvCorrectionInputWidget(QWidget):

    submitted = pyqtSignal(object)

    def __init__(self, parent=None):
        super(DiDvCorrectionInputWidget, self).__init__()

        # A reference to a parent object
        self.parent = parent

        self.datasets = self.parent.parent.datasets

        self.init_ui()

    def init_ui(self):
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        self.setGeometry(int(0.2 * width), int(0.2 * height), 300, 200)

        self.setWindowTitle("Ola senor !")
        self.setWindowIcon(QIcon("img/question_mark_icon.png"))

        v_layout = QVBoxLayout()
        self.explanation_text_label = QLabel("Please input resistance and dV that will be used in calculating dV(real)")
        v_layout.addWidget(self.explanation_text_label)

        self.matrices_dropdown = QComboBox()

        self.dataset_dropdown_label = QLabel("Select dataset to load matrix from.")
        v_layout.addWidget(self.dataset_dropdown_label)
        self.dataset_dropdown = QComboBox()
        for name, dataset_object in self.datasets.items():
            self.dataset_dropdown.addItem(name, dataset_object)
        self.dataset_dropdown.currentIndexChanged.connect(self.update_matrices)
        self.update_matrices()

        h_layout_dataset_selection = QHBoxLayout()
        h_layout_dataset_selection.addWidget(self.dataset_dropdown)
        h_layout_dataset_selection.addWidget(self.matrices_dropdown)

        self.resistance = QLineEdit("")
        self.resistance.setPlaceholderText("Resistance")

        self.d_v = QLineEdit("")
        self.d_v.setPlaceholderText("dV")

        self.submit_btn = QPushButton("OK")
        self.submit_btn.clicked.connect(self.submit_data)

        v_layout.addLayout(h_layout_dataset_selection)
        v_layout.addWidget(self.resistance)
        v_layout.addWidget(self.d_v)
        v_layout.addWidget(self.submit_btn)

        self.setLayout(v_layout)
        self.show()

    def update_matrices(self):
        self.matrices_dropdown.clear()
        matrices = self.dataset_dropdown.currentData().get_matrix()
        for index, matrix in enumerate(matrices):
            self.matrices_dropdown.addItem("matrix{}".format(index), matrix)


    def submit_data(self):
        # do stuff
        send_value = []
        if is_numeric(self.resistance.text()):
            send_value.append(self.resistance.text())
        else:
            show_error_message("Warning", "Input data has to be numeric")
            return

        if is_numeric(self.d_v.text()):
            send_value.append(self.d_v.text())
        else:
            show_error_message("Warning", "Input data has to be numeric")
            return

        matrix = self.matrices_dropdown.currentData()
        send_value.append(matrix)

        self.submitted.emit(send_value)
        self.close()
