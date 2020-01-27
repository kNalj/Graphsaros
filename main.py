from PyQt5.QtWidgets import QApplication, QMainWindow, QGridLayout, QDesktopWidget, QPushButton, QWidget, QTableWidget,\
    QTextBrowser, QAction, QMenu, QFileDialog, QHeaderView, QTableWidgetItem, QSizePolicy, QVBoxLayout
from PyQt5 import QtCore, QtGui

from data_handlers import LabberDataBuffer, QcodesDataBuffer, QtLabDataBuffer, MatrixFileDataBuffer
from widgets import ProgressBarWidget
from widgets.BufferExplorer import BufferExplorer
from graphs.Heatmap import Heatmap
from graphs.LineTrace import LineTrace
from ThreadWorker import Worker
from helpers import get_location_basename
from debug.errors import ErrorHandler

import pyqtgraph as pg

import sys
import os


def trap_exc_during_debug(*args):
    # when app raises uncaught exception, print info
    eh = ErrorHandler("Exception trap triggered. ", args[0], args[1], args[2])
    eh.to_file()
    eh.print_full_report()


# install exception hook: without this, uncaught exception would cause application to exit
sys.excepthook = trap_exc_during_debug


class MainWindow(QMainWindow):
    def __init__(self):
        """
        Starting window of Graphsaros app. Enables user to load and select among loaded DataBuffers.

        """
        super().__init__()
        print("Instantiating main window . . .")
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

        self.thread_pool = QtCore.QThreadPool()

        # call to a method that builds user interface
        self.init_ui()
        # call to a method that builds menu bar
        self.init_manu_bar()
        # after the interface has been built, show the window
        self.show()

    def init_ui(self):
        """

        :return:
        """

        print("Modeling main window . . .")
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

        print("Building datasets table . . .")
        # table widget containing all loaded data sets
        self.opened_datasets_tablewidget = QTableWidget(0, 4)
        self.opened_datasets_tablewidget.setMinimumSize(600, 200)
        self.opened_datasets_tablewidget.setHorizontalHeaderLabels(("Name", "Location", "Delete", "Type"))
        self.opened_datasets_tablewidget.doubleClicked.connect(self.display_dataset)
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

        print("Building mini plot . . .")
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

        self.loading_bars_layout = QVBoxLayout()

        # position the elements within the grid layout
        self.grid_layout.addWidget(self.opened_datasets_tablewidget, 0, 0, 1, 3)
        self.grid_layout.addWidget(self.selected_dataset_textbrowser, 1, 0, 3, 1)
        self.grid_layout.addWidget(preview_plt, 1, 1, 1, 2)
        self.grid_layout.addWidget(self.add_to_list_btn, 2, 1, 1, 2)
        self.grid_layout.addWidget(self.open_dataset_btn, 3, 1, 1, 1)
        self.grid_layout.addWidget(self.exit_btn, 3, 2, 1, 1)
        self.grid_layout.addLayout(self.loading_bars_layout, 4, 0, 1, 3)

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
        print("Modeling menu bar . . .")
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
        print("Closing all windows and exiting the application . . .")
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

    def keyPressEvent(self, qKeyEvent):
        """

        :param qKeyEvent:
        :return:
        """
        if qKeyEvent.key() in [QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
            self.display_dataset()
        else:
            super().keyPressEvent(qKeyEvent)

    def open_file_dialog(self):
        """
        Opens a file dialog for selecting file to load into application. Depending on type of file the headers of the
        files differ allowing to recognize which type of DataBuffer needs to be instantiated.

        :return: NoneType
        """
        print("Opening FileDialog for selecting files . . .")
        file_dialog = QFileDialog.getOpenFileNames()

        for file in file_dialog[0]:
            name = get_location_basename(os.path.dirname(file))
            with open(file, "r") as current_file:
                if file.lower().endswith(".hdf5"):
                    type_item = QTableWidgetItem("Labber")
                    buffer = LabberDataBuffer.LabberData(file)
                    worker = Worker(buffer.prepare_data)
                    progress_bar = self.add_progress_widget(buffer)
                    buffer.progress.connect(lambda progress: self.get_progress(progress, progress_bar))
                    self.datasets[name] = buffer
                    buffer.ready.connect(self.make_add_to_table(self.datasets[name]))
                    worker.signals.finished.connect(lambda: self.add_buffer_to_table(self.datasets[name],
                                                                                     type_item))
                    self.thread_pool.start(worker)
                else:
                    for i, line in enumerate(current_file):
                        if i == 2:
                            if line.strip(" \n") == "":
                                type_item = QTableWidgetItem("QtLab")
                                buffer = QtLabDataBuffer.QtLabData(file)
                                worker = Worker(buffer.prepare_data)
                            elif line.startswith("#"):
                                type_item = QTableWidgetItem("QCoDeS")
                                buffer = QcodesDataBuffer.QcodesData(file)
                                worker = Worker(buffer.prepare_data)
                            else:
                                type_item = QTableWidgetItem("Matrix")
                                buffer = MatrixFileDataBuffer.MatrixData(file)
                                worker = Worker(buffer.prepare_data)

                            progress_bar = self.add_progress_widget(buffer)
                            buffer.progress.connect(lambda progress: self.get_progress(progress, progress_bar))
                            self.datasets[name] = buffer
                            buffer.ready.connect(self.make_add_to_table(self.datasets[name]))
                            worker.signals.finished.connect(lambda: self.add_buffer_to_table(self.datasets[name],
                                                                                             type_item))
                            self.thread_pool.start(worker)

                            break

    def add_progress_widget(self, buffer):
        """
        Adds a progress bar that tracks the loading process of data in the data buffer

        :param buffer: DataBuffer: a reference to a data buffer that is being loaded into the program
        :return: a reference to a newly created progress bar widget
        """
        print("Loading data buffer . . .")
        progress_bar = ProgressBarWidget.ProgressBarWidget(buffer.name)
        progress_bar.finished.connect(self.remove_progress_widget)
        self.loading_bars_layout.addWidget(progress_bar)

        return progress_bar

    def remove_progress_widget(self, widget):
        """
        Removes the progress bar after the data buffer has finished loading

        :param widget: a reference to a progress bar that needs to be removed from the main window
        :return: NoneType
        """
        widget.deleteLater()
        return

    def get_progress(self, progress, progress_bar):
        """
        DataBuffers prepare_data() method emits a progress signal while its loading data, this signal carries a value
        from 0 to 1 (percentage) and get_progress() takes this number and sets to progress bar widgets value to that
        number multiplied by a 100.

        :param progress: float: a number between 0 and 1 that signals the percentage of loaded data
        :param progress_bar: a reference to a progress bar widget that needs to be updated
        :return: NoneType
        """
        progress_bar.setValue(progress*100)
        return

    def make_add_to_table(self, buffer):
        """
        Function factory used to create functions enable adding a loaded data buffer to a table of data buffers

        :param buffer: a reference to a data buffer that is going to be added to the table
        :return: pointer to a function created in this function factory
        """
        def add_to_table():
            self.add_buffer_to_table(buffer)
        return add_to_table

    def add_buffer_to_table(self, buffer, item_type=None):
        """
        Actual method that creates a row in the table in the main window and adds the data buffer to that table.

        :param buffer: DataBuffer(): instance of data buffer that is being added to the table in the main window
        :param item_type: string: string that is added to table to display type of the buffer in that row
        :return: NoneType
        """
        print("Adding buffer to the table . . .")
        if buffer.is_data_ready():
            name = get_location_basename(os.path.dirname(buffer.get_location()))
            rows = self.opened_datasets_tablewidget.rowCount()
            self.opened_datasets_tablewidget.insertRow(rows)
            table_item = QTableWidgetItem(name)
            table_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.opened_datasets_tablewidget.setItem(rows, 0, table_item)
            location_item = QTableWidgetItem(buffer.get_location())
            location_item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
            self.opened_datasets_tablewidget.setItem(rows, 1, location_item)
            delete_current_file_btn = QPushButton("Delete")
            delete_current_file_btn.clicked.connect(self.make_delete_file_from_list(location_item))
            self.opened_datasets_tablewidget.setCellWidget(rows, 2, delete_current_file_btn)
            self.opened_datasets_tablewidget.setItem(rows, 3, item_type)
            print("Added to the table . . .")
        else:
            print("Data not ready ! Abort.")

    def display_dataset(self):
        """
        TODO: Keep traack of all opened windows separately, currently the older ones are overwritten by newer ones
        A method that opens LineTrace or Heatmap window depending on number of dimension that the selected buffer has.

        :return: NoneType
        """
        row = self.opened_datasets_tablewidget.currentRow()
        if row != -1:
            item = self.opened_datasets_tablewidget.item(row, 1)
            location = item.text()
            name = get_location_basename(os.path.dirname(location))
            dataset = self.datasets[name]

            if dataset.get_number_of_dimension() == 3:
                self.hm = Heatmap(dataset, self)
                self.hm.show()
            else:
                self.lt = LineTrace(dataset, None)
                self.lt.show()

    def open(self, file_type: str):
        """
        Needs to be implemented, opens a speciified type of file

        :param file_type: string: specifies the type of file that we are trying to open
        :return: I DONT KNOW WHAT WILL IT DO YET, HAVENT REALLY TOUGHT ABOUT IT
        """
        print(file_type)

    def make_delete_file_from_list(self, item):
        """
        Function factory that creates and returns a function that removes a databuffer from databuffer table

        :param item: item to be removed
        :return: Pointer to a function that removes a row from the table
        """

        def delete_file_from_list():
            self.opened_datasets_tablewidget.removeRow(self.opened_datasets_tablewidget.row(item))

        return delete_file_from_list

    def refresh_main_view(self):
        """
        Helper method that calls all necessary method needed to update display of the main window once different data
        buffer was selected from table of data buffers.

        :return: NonType
        """
        print("Redrawing main window . . .")
        self.update_mini_graph()
        self.update_text_display()

    def update_mini_graph(self):
        """
        Updates displayed data in the miniature graph area on the main window to display data of the selected data
        buffer. It is called upon changing selection in the table of buffers in main window.

        :return: NoneType
        """
        print("Updating mini graph . . .")
        row = self.opened_datasets_tablewidget.currentRow()
        if row != -1:
            item = self.opened_datasets_tablewidget.item(row, 1)
            location = item.text()
            name = get_location_basename(os.path.dirname(location))
            dataset = self.datasets[name]

            if dataset.get_number_of_dimension() == 2:
                print(" Drawing 2d plot . . .")
                self.mini_plot_items["main_subplot"].clear()
                self.mini_plot_items["main_subplot"].plot(x=dataset.get_x_axis_values(),
                                                          y=dataset.get_y_axis_values()[0],
                                                          pen=(60, 60, 60))
            else:
                print(" Drawing 3d plot . . .")
                self.mini_plot_items["main_subplot"].clear()
                print(" Fetching image data . . .")
                img = pg.ImageItem()
                img.setImage(dataset.get_matrix(index=0))
                (x_scale, y_scale) = dataset.get_scale()
                img.translate(dataset.get_x_axis_values()[0], dataset.get_y_axis_values()[0][0])
                img.scale(x_scale, y_scale)
                print(" Drawing histogram . . .")
                histogram = pg.HistogramLUTItem()
                histogram.setImageItem(img)
                histogram.gradient.loadPreset("thermal")
                self.mini_plot_items["main_subplot"].addItem(img)

                print(" Drawing axes . . .")
                legend = {"left": "y", "bottom": "x"}
                for side in ('left', 'bottom'):
                    ax = self.mini_plot_items["main_subplot"].getAxis(side)
                    ax.setPen((60, 60, 60))
                    if legend[side] == "y":
                        axis_data = self.datasets[name].axis_values[legend[side]][0]
                    else:
                        axis_data = self.datasets[name].axis_values[legend[side]]
                    label_style = {'font-size': '7pt'}
                    ax.setLabel(axis_data["name"], axis_data["unit"], **label_style)

    def update_text_display(self):
        """
        Updates displayed data in the text browser area of the main window to display data of the selected data buffer.
        It is called upon changing selection in the table of buffers in main window.

        :return: NoneType
        """
        print("Updating text display . . .")
        self.selected_dataset_textbrowser.clear()
        row = self.opened_datasets_tablewidget.currentRow()
        if row != -1:
            item = self.opened_datasets_tablewidget.item(row, 1)
            location = item.text()
            name = get_location_basename(os.path.dirname(location))
            dataset = self.datasets[name]

            self.selected_dataset_textbrowser.append("X:\n\t[Name: {}]\n\t[Unit: {}]\n\t[Step: {}]\n".format(
                dataset.axis_values["x"]["name"],
                dataset.axis_values["x"]["unit"],
                (dataset.get_x_axis_values()[-1] - dataset.get_x_axis_values()[0]) / len(dataset.get_x_axis_values()) - 1))
            self.selected_dataset_textbrowser.append("Y:\n\t[Name: {}]\n\t[Unit: {}]\n\t[Step: {}]\n".format(
                dataset.axis_values["y"][0]["name"],
                dataset.axis_values["y"][0]["unit"],
                (dataset.get_y_axis_values()[0][-1] - dataset.get_y_axis_values()[0][0]) / len(dataset.get_y_axis_values()[0]) - 1))
            self.selected_dataset_textbrowser.append("Matrix:\n {}".format(dataset.textual_data_representation()))

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
            self.add_buffer_to_table(buffer, QTableWidgetItem(buffer.string_type))
            name = get_location_basename(os.path.dirname(buffer.get_location()))
            self.datasets[name] = buffer


def main():

    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
