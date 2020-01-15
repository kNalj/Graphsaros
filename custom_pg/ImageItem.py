# I am not an author of this code. This code is a part of a pyqtgraph_extensions package
# Reference: https://pypi.org/project/pyqtgraph-extensions/
# Distributed under BSD license

import logging
import pyqtgraph as pg
import numpy as np
from pyqtgraph import QtCore

logger = logging.getLogger(__name__)


class ImageItem(pg.ImageItem):
    sigLevelsChanged = QtCore.Signal()
    sigLookupTableChanged = QtCore.Signal()

    def __init__(self, image=None, **kargs):
        pg.ImageItem.__init__(self, image, **kargs)

    def setLevels(self, levels, update=True):
        """
        Set image scaling levels. Can be one of:

        * [blackLevel, whiteLevel]
        * [[minRed, maxRed], [minGreen, maxGreen], [minBlue, maxBlue]]

        Only the first format is compatible with lookup tables. See :func:`makeARGB <pyqtgraph.makeARGB>`
        for more details on how levels are applied.
        """
        emit = self.levels is None or not np.allclose(self.levels, levels)
        pg.ImageItem.setLevels(self, levels, update)
        if emit:
            self.sigLevelsChanged.emit()

    def setLookupTable(self, lut, update=True, emit=True):
        """
        Set the lookup table (numpy array) to use for this image. (see
        :func:`makeARGB <pyqtgraph.makeARGB>` for more information on how this is used).
        Optionally, lut can be a callable that accepts the current image as an
        argument and returns the lookup table to use.

        Ordinarily, this table is supplied by a :class:`HistogramLUTItem <pyqtgraph.HistogramLUTItem>`
        or :class:`GradientEditorItem <pyqtgraph.GradientEditorItem>`.
        """
        pg.ImageItem.setLookupTable(self, lut, update)
        if emit:
            self.sigLookupTableChanged.emit()

    def setImage(self, image=None, autoLevels=True, levels=None, **kwargs):
        """
        Add behaviour that if autoLevels is False and levels is None, levels
        is set to current (if that is not None). (In original, this causes an error.)

        :param image:
        :param autoLevels:
        :param levels:
        :param kwargs:
        :return:
        """
        if levels is None and not autoLevels:
            if self.levels is not None:
                logger.debug('setImage retaining levels')
                levels = self.levels
            else:
                autoLevels = True
        pg.ImageItem.setImage(self, image=image, autoLevels=autoLevels, levels=levels, **kwargs)