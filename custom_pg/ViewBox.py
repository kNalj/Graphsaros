# I am not an author of this code. This code is a part of a pyqtgraph_extensions package
# Reference: https://pypi.org/project/pyqtgraph-extensions/
# Distributed under BSD license

import pyqtgraph as pg


class ViewBox(pg.ViewBox):
    """Convenience extension of ViewBox providing:

        * plot function (necessary for seamless use of pyqtgraph.add_right_axis)
        * ability to override the default padding, which is used by enableAutoRange
    """

    def __init__(self, **kwargs):
        pg.ViewBox.__init__(self, **kwargs)
        self.suggested_padding = [None, None]

    def plot(self, *args, **kargs):
        """
        Add and return a new plot.
        See :func:`PlotDataItem.__init__ <pyqtgraph.PlotDataItem.__init__>` for data arguments
        """
        item = pg.PlotDataItem(*args, **kargs)
        self.addItem(item)
        return item

    def suggestPadding(self, axis):
        suggested = self.suggested_padding[axis]
        if suggested is None:
            return pg.ViewBox.suggestPadding(self, axis)
        else:
            return suggested
