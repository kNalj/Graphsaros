from PyQt5.QtWidgets import QMainWindow


class BaseGraph(QMainWindow):

    """
    Base class for graphs in Graphsaros app.

    """

    def __init__(self, parent=None):
        """
        Base class for windows that display 2d and 3D graphs

        """
        super().__init__()

        self.parent = parent

        # plot object, can be 2D or 3D
        self.plt = None

    def init_ui(self):
        """
        Should be implemented in the child classes. Defines the interface of the widget.

        :return: NoneType
        """
        raise NotImplementedError

    def init_toolbar(self):
        """
        Should be implemented in the child classes. Defines toolbar and its actions for all widgets that inherit from
        this one.

        :return: NoneType
        """
        raise NotImplementedError

    def perform_action(self, action):
        """
        Gets the name of the action that called this method. Then from the name of the action creates the name of the
        method that is supposed to be called by that action. For every action with a name there is a method with name:
        name_action that gets called upon triggering that action from toolbar.

        :param action: string: name of the action to be performed
        :return: NoneType
        """
        method_name = action.text().lower()
        method_name = method_name + "_action"
        action_method = getattr(self, method_name)
        action_method()

    def exit_action(self):
        self.close()
