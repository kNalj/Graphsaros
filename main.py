from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QDesktopWidget, QPushButton, QWidget, QTableWidget,\
    QTextBrowser, QAction, QMenu, QFileDialog, QHeaderView, QTableWidgetItem, QSizePolicy
from PyQt5 import QtCore, QtGui

from data_handlers.QtLabDataBuffer import QtLabData
from data_handlers.QcodesDataBuffer import QcodesData
from data_handlers.MatrixFileDataBuffer import MatrixData
from BufferExplorer import BufferExplorer
from graphs.Heatmap import Heatmap
from graphs.LineTrace import LineTrace

import pyqtgraph as pg

import sys
import os


def trap_exc_during_debug(exctype, value, traceback, *args):
    # when app raises uncaught exception, print info
    print(args)
    print(exctype, value, traceback)


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class MainWindow(QMainWindow):
    def __init__(self):
        """
        Starting window of Graphsaros app. Enables user to load and select among loaded DataBuffers.

        """
        super().__init__()

        # define title of the window
        self.title = "Graphsaros"
        # define width of the window
        self.width = 840
        # define height of th window
        self.height = 460

        # QMainWindow by default has defined layout which defines central widget as a place where
        # to add your widgets (buttons, text, etc.), so in order to be able to customize it we
        # to create central widget and set grid layout to it, then we can do what we want
        self.centralWidget = QWidget()

        # dict of data sets that have been loaded into the main program
        self.datasets = {}

        # call to a method that builds user interface
        self.init_ui()
        # call to a method that builds menu bar
        self.init_manu_bar()
        # after the interface has been built, show the window
        self.show()

    def init_ui(self):

        # find dimensions of the monitor (screen)
        _, _, width, height = QDesktopWidget().screenGeometry().getCoords()
        # set position of the window relative to the dimensions of the display screen
        self.setGeometry(int(0.02 * width), int(0.05 * height), self.width, self.height)
        # set the title of the window
        self.setWindowTitle(self.title)
        # set the icon of the window
        self.setWindowIcon(QtGui.QIcon("img/graph.png"))

        # define the layout for central widget
        self.grid_layout = QGridLayout()

        # create elements of the central widget
        self.add_to_list_btn = QPushButton("Open")
        self.add_to_list_btn.clicked.connect(self.open_file_dialog)

        # button for closing the application and all of its windows
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.exit)

        # Button for opening detailed view of the specified data set
        self.open_dataset_btn = QPushButton("Plot")
        self.open_dataset_btn.clicked.connect(self.display_dataset)

        # table widget containing all loaded data sets
        self.opened_datasets_tablewidget = QTableWidget(0, 4)
        self.opened_datasets_tablewidget.setMinimumSize(600, 200)
        self.opened_datasets_tablewidget.setHorizontalHeaderLabels(("Name", "Location", "Delete", "Type"))
        header = self.opened_datasets_tablewidget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.opened_datasets_tablewidget.setSelectionBehavior(QTableWidget.SelectRows)

        # text browser for displaying samo basic data about the selected data set
        self.selected_dataset_textbrowser = QTextBrowser()
        self.selected_dataset_textbrowser.setMinimumSize(600, 200)
        self.selected_dataset_textbrowser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # miniature plot that displays data of the selected buffer
        preview_plt = pg.GraphicsView()
        mini_plot = pg.GraphicsLayout()
        main_subplot = mini_plot.addPlot()
        for axis in ["left", "bottom"]:
            ax = main_subplot.getAxis(axis)
            ax.setPen((60, 60, 60))

        preview_plt.setCentralItem(mini_plot)
        preview_plt.setBackground('w')

        self.mini_plot_items = {"main_subplot": main_subplot}

        # position the elements within the grid layout
        self.grid_layout.addWidget(self.opened_datasets_tablewidget, 0, 0, 1, 3)
        self.grid_layout.addWidget(self.selected_dataset_textbrowser, 1, 0, 3, 1)
        self.grid_layout.addWidget(preview_plt, 1, 1, 1, 2)
        self.grid_layout.addWidget(self.add_to_list_btn, 2, 1, 1, 2)
        self.grid_layout.addWidget(self.open_dataset_btn, 3, 1, 1, 1)
        self.grid_layout.addWidget(self.exit_btn, 3, 2, 1, 1)

        # connect changing a selected set in the table to a method that displays correct data in the text browser and
        # in the mini plot
        self.opened_datasets_tablewidget.currentCellChanged.connect(self.refresh_main_view)

        # set the layout of the central widget
        self.centralWidget.setLayout(self.grid_layout)
        # set central widget to be THE CENTRAL WIDGET (QMainWindow predefined element)
        self.setCentralWidget(self.centralWidget)

    def init_manu_bar(self):
        """
        Initialize menu bar of main window.

        :return: NoneType
        """

        # create action for closing the program
        exit_action = QAction("&Exit", self)
        # add shortcut to this action
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        # connect action to exit method
        exit_action.triggered.connect(self.exit)

        # menu entry for opening different data (buffer) types
        open_action = QMenu("&Open", self)

        # set of actions each one used to open a specific data (buffer) type
        open_qcodes = QAction("&Open QCoDeS", self)
        open_qcodes.triggered.connect(lambda: self.open("qcodes"))
        open_qtlab = QAction("&Open QtLab", self)
        open_qtlab.triggered.connect(lambda: self.open("qtlab"))
        open_matrix = QAction("&Open matrix", self)
        open_matrix.triggered.connect(lambda: self.open("matrix"))

        open_action.addAction(open_qcodes)
        open_action.addAction(open_qtlab)
        open_action.addAction(open_matrix)

        # action that opens a window that enables user to load multiple buffers from within a folder
        open_folder_explorer = QAction("&Folder explorer", self)
        open_folder_explorer.triggered.connect(self.open_folder_explorer)

        # create menu bar
        menu_bar = self.menuBar()
        # add submenu
        file_menu = menu_bar.addMenu("&File")
        # add action to the FILE submenu
        file_menu.addAction(open_folder_explorer)
        file_menu.addMenu(open_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

    def exit(self):
        """
        Method called upon closing main window. Closes all other windows belongig to this application

        :return:
        """
        app = QtGui.QGuiApplication.instance()
        app.closeAllWindows()
        self.close()

    def closeEvent(self, *args, **kwargs):
        """
        Event that is triggered upon closing main window. Calls a method that closes all windows belongig to this app.

        :param args:
        :param kwargs:
        :return:
        """
        self.exit()

    def open_file_dialog(self):
        """
        Opens a file dialog for selecting file to load into application. Depending on type of file the headers of the
        files differ allowing to recognize which type of DataBuffer needs to be instantiated.

        :return: NoneType
        """
        file_dialog = QFileDialog.getOpenFileNames()

        for file in file_dialog[0]:

            name = os.path.basename(file)
            rows = self.opened_datasets_tablewidget.rowCount()

            with open(file, "r") as current_file:
                for i, line in enumerate(current_file):
                    if i == 2:
                        if line.strip(" \n") == "":
                            self.datasets[name] = QtLabData(file)
                            self.datasets[name].ready.connect(self.make_add_to_table(self.datasets[name]))
                            type_item = QTableWidgetItem("QtLab")
                        elif line.startswith("#"):
                            self.datasets[name] = QcodesData(file)
                            self.datasets[name].ready.connect(self.make_add_to_table(self.datasets[name]))
                            type_item = QTableWidgetItem("QCoDeS")
                        else:
                            self.datasets[name] = MatrixData(file)
                            self.datasets[name].ready.connect(self.make_add_to_table(self.datasets[name]))
                            type_item = QTableWidgetItem("Matrix")
                        self.opened_datasets_tablewidget.setItem(rows, 3, type_item)

                        break
            self.add_buffer_to_table(self.datasets[name])

    def make_add_to_table(self, buffer):
        """
        Function factory used to create functions enable adding a loaded data buffer to a table of data buffers

        :param buffer:
        :return: pointer to a function created in this function factory
        """
        def add_to_table():
            self.add_buffer_to_table(buffer)
        return add_to_table

    def add_buffer_to_table(self, buffer):
        """
        Actual method that creates a row in the table in the main window and adds the data buffer to that table.

        :param buffer: DataBuffer(): instance of data buffer that is being added to the table in the main window
        :return: NoneType
        """
        if buffer.is_data_ready():
            name = os.path.basename(buffer.get_location())
            rows = self.opened_datasets_tablewidget.rowCount()
            self.opened_datasets_tablewidget.insertRow(rows)
            name_item = QTableWidgetItem(name)
            name_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.opened_datasets_tablewidget.setItem(rows, 0, name_item)
            location_item = QTableWidgetItem(buffer.get_location())
            location_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.opened_datasets_tablewidget.setItem(rows, 1, location_item)
            delete_current_file_btn = QPushButton("Delete")
            delete_current_file_btn.clicked.connect(self.make_delete_file_from_list(name_item))
            self.opened_datasets_tablewidget.setCellWidget(rows, 2, delete_current_file_btn)
        else:
            print("WHY")

    def display_dataset(self):
        """
        A method that opens LineTrace or Heatmap window depending on number of dimension that the selected buffer has.

        :return: NoneType
        """
        row = self.opened_datasets_tablewidget.currentRow()
        if row != -1:
            item = self.opened_datasets_tablewidget.item(row, 1)
            location = item.text()
            name = os.path.basename(location)
            dataset = self.datasets[name]

            if dataset.get_number_of_dimension() == 3:
                self.hm = Heatmap(dataset)
                self.hm.show()
            else:
                self.lt = LineTrace(dataset)
                self.lt.show()

    def open(self, file_type: str):
        """
        Needs to be implemented, opens a speciified type of file

        :param file_type: string: specifies the type of file that we are trying to open
        :return: I DONT KNOW WHAT WILL IT DO YET, HAVENT REALLY TOUGHT ABOUT IT
        """
        print(file_type)

    def make_delete_file_from_list(self, name: str):
        """
        Function factory that creates and returns a function that removes a databuffer from databuffer table

        :param name: name of the data buffer ( one used in the table )
        :return: Pointer to a function that removes a row from the table
        """

        def delete_file_from_list():
            self.opened_datasets_tablewidget.removeRow(self.opened_datasets_tablewidget.row(name))

        return delete_file_from_list

    def refresh_main_view(self):
        """
        Helper method that calls all necessary method needed to update display of the main window once different data
        buffer was selected from table of data buffers.

        :return: NonType
        """
        self.update_mini_graph()
        self.update_text_display()

    def update_mini_graph(self):
        """
        Updates displayed data in the miniature graph area on the main window to display data of the selected data
        buffer. It is called upon changing selection in the table of buffers in main window.

        :return: NoneType
        """
        row = self.opened_datasets_tablewidget.currentRow()
        if row != -1:
            item = self.opened_datasets_tablewidget.item(row, 1)
            location = item.text()
            name = os.path.basename(location)
            dataset = self.datasets[name]

            if dataset.get_number_of_dimension() == 2:
                self.mini_plot_items["main_subplot"].clear()
                self.mini_plot_items["main_subplot"].plot(x=dataset.get_x_axis_values(),
                                                          y=dataset.get_y_axis_values(),
                                                          pen=(60, 60, 60))
            else:
                self.mini_plot_items["main_subplot"].clear()
                img = pg.ImageItem()
                img.setImage(dataset.get_matrix(index=0))
                (x_scale, y_scale) = dataset.get_scale()
                img.translate(dataset.get_x_axis_values()[0], dataset.get_y_axis_values()[0])
                img.scale(x_scale, y_scale)
                histogram = pg.HistogramLUTItem()
                histogram.setImageItem(img)
                histogram.gradient.loadPreset("thermal")
                self.mini_plot_items["main_subplot"].addItem(img)

                legend = {"left": "y", "bottom": "x"}
                for side in ('left', 'bottom'):
                    ax = self.mini_plot_items["main_subplot"].getAxis(side)
                    ax.setPen((60, 60, 60))
                    axis_data = self.datasets[name].axis_values[legend[side]]
                    label_style = {'font-size': '7pt'}
                    ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

    def update_text_display(self):
        """
        Updates displayed data in the text browser area of the main window to display data of the selected data buffer.
        It is called upon changing selection in the table of buffers in main window.

        :return: NoneType
        """
        self.selected_dataset_textbrowser.clear()
        row = self.opened_datasets_tablewidget.currentRow()
        if row != -1:
            item = self.opened_datasets_tablewidget.item(row, 1)
            location = item.text()
            name = os.path.basename(location)
            dataset = self.datasets[name]

            self.selected_dataset_textbrowser.append("X [Step: {}]\tY [Step: {}]".format(
                dataset.get_x_axis_values()[1] - dataset.get_x_axis_values()[0],
                dataset.get_y_axis_values()[1] - dataset.get_y_axis_values()[0]))
            self.selected_dataset_textbrowser.append(dataset.textual_data_representation())

    def open_folder_explorer(self):
        """
        Method that opens a file explorer widget and lets you select one folder from it. It instantiates a
        BufferExplorer widget with files found within the selected folder.

        :return: NoneType
        """
        folder = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if folder:
            self.be = BufferExplorer(folder)
            self.be.submitted.connect(self.get_buffers_from_signal)
            self.be.add_requested.connect(self.get_buffers_from_signal)

    def get_buffers_from_signal(self, buffers):
        """
        Slot that gets data from BufferExplorers signals and adds buffers to the main window opened_datasets_table

        :param buffers: dictionary: contins key: string representation of the buffers location on file system
                                            value: instance of DataBuffer
        :return: NoneType
        """
        for path, buffer in buffers.items():
            self.add_buffer_to_table(buffer)
            name = os.path.basename(buffer.get_location())
            self.datasets[name] = buffer


def main():
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
