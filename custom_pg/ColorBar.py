# I am not an author of this code. This code is a part of a pyqtgraph_extensions package
# Reference: https://pypi.org/project/pyqtgraph-extensions/
# Distributed under BSD license

import logging
import pyqtgraph as pg
import numpy as np
from custom_pg.ViewBox import ViewBox
from custom_pg.AxisItem import AxisItem
from pyqtgraph import QtCore, QtGui

logger = logging.getLogger(__name__)


class ColorBarItem(pg.GraphicsWidget):
    """A color bar for an ImageItem.

    Vertical, with AxisItem for scale on the right side (could be extended to
    other orientations and scale on other side).

    Has two modes. If self.image is None, then it is in manual mode. The LUT and
    levels are set by setManual. Otherwise, it is is in automatic mode, linked to
    self.image, which must be a pgx.ImageItem. It responds to changes in the
    image's lookup table, levels and range. The user can adjust the axis with the
    mouse like a normal axis. Autoscaling works.

    The implementation uses a viewbox containing an imageitem with an axisitem
    beside it. The imageitem vertical extent is set to the color range of the image.
    In this way, the autorange functionality of the viewbox and axisitem are
    put to use. It's probably not optimally efficient.
    """

    def __init__(self, parent=None, image=None, label=None, images=()):
        pg.GraphicsWidget.__init__(self, parent)
        """Previous version used manual layout. This worked for initial setup but
        I couldn't figure out how to make it update automatically if e.g. the
        axis width changed. So switched to layout management. This requires
        the ImageItem to be in a QGraphicsLayoutItem, since it is not one itself.
        Putting it in a ViewBox seemed the simplest option."""
        # Backwards compatilbility: retain image argument
        if image is not None:
            assert images == ()
            images = (image,)
        images = tuple(images)
        # Setup layout
        self.layout = QtGui.QGraphicsGridLayout()
        self.layout.setHorizontalSpacing(0)
        self.layout.setVerticalSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        # Setup ViewBox containing the colorbar
        self.vb = ViewBox()
        self.vb.setFixedWidth(10)
        self.vb.setLimits(xMin=0, xMax=1)
        self.vb.setMouseEnabled(x=False)
        self.vb.suggested_padding[1] = 0
        # Setup colorbar, implemented as an ImageItem
        self.bar = pg.ImageItem()
        # The color bar ImageItem levels run from 0 to 1
        self.bar.setImage(np.linspace(0, 1, 8192)[None, :])
        self.vb.addItem(self.bar)
        self.layout.addItem(self.vb, 0, 0)
        # Setup axis
        self.axis = AxisItem(orientation='right')
        self.axis.linkToView(self.vb)
        self.axis.range_changed.connect(self.axis_to_levels)
        self.layout.addItem(self.axis, 0, 1)
        self.setLayout(self.layout)
        self.images = ()
        self.images_min = {}
        self.images_max = {}
        self.manual_lut = None
        self.manual_levels = None
        self.setImages(images)
        if label is not None:
            self.setLabel(label)

    def setLabel(self, label):
        self.axis.setLabel(label)

    def setImages(self, images):
        for image in self.images:
            # Hack - this connects all slots.
            image.sigLevelsChanged.disconnect()
            image.sigImageChanged.disconnect()
            image.sigLookupTableChanged.disconnect()
        self.images = images
        if self.images != ():
            self.update()  # what does this do?
            self.lookupTableChanged(images[0])
            self.imageRangeChanged(images)
            for image in self.images:
                image.sigLevelsChanged.connect(lambda image=image: self.imageLevelsChanged(image))
                image.sigImageChanged.connect(lambda image=image: self.imageRangeChanged([image]))
                image.sigLookupTableChanged.connect(lambda image=image: self.lookupTableChanged(image))
            # self.vb.enableAutoRange(axis=1)
        else:
            self.updateManual()
        self.vb.setMouseEnabled(y=self.images != ())
        self.axis.setButtonsEnabled(self.images != ())
        # Found that without this, setting an image after ColorBarItem.__init__
        # was triggering an update auto range in the AxisItem, which screwed
        # up the level setting. Updating clears the ViewBox's internal flag.
        self.vb.updateAutoRange()

    def setImage(self, image):
        self.setImages((image,))

    def lookupTableChanged(self, image):
        """Sets the lookup table based on zeroth image."""
        self.bar.setLookupTable(image.lut)
        for im in self.images:
            if image is im:
                continue
            # When setting co-linked images, don't want them to emit the signal.
            im.setLookupTable(image.lut, emit=False)

    def imageRangeChanged(self, images):
        """Respond to change in the range of the images."""
        for image in images:
            image_data = image.image
            if image_data is None:
                return
            self.images_min[image] = image_data.min()
            self.images_max[image] = image_data.max()
        self.image_min = min(self.images_min.values())
        self.image_max = max(self.images_max.values())
        # Set spatial extent of bar to range of image
        logger.debug('setting bar extent to %g,%g', self.image_min, self.image_max)
        self.bar.setRect(QtCore.QRectF(0, self.image_min, 1, self.image_max - self.image_min))
        self.updateBarLevels()

    def imageLevelsChanged(self, image):
        if not np.allclose(self.vb.viewRange()[1], image.levels):
            logger.debug('setYRange %g,%g', *image.levels)
            assert len(image.levels) == 2
            if all(np.isfinite(image.levels)):
                self.vb.setYRange(*image.levels, padding=0)
            else:
                logger.info('skipping setYRange because np.levels is %s' % str(image.levels))
        self.updateBarLevels()

    def updateBarLevels(self):
        """Update the levels of the bar ImageItem from the image.

        These depend on both the image levels and the image range."""
        # Assume all images have same level
        image_levels = self.images[0].levels
        if not hasattr(self, 'image_max'):
            # range has not been set yet
            return
        image_range = self.image_max - self.image_min
        if image_range == 0:
            bar_levels = 0, 0
        else:
            bar_levels = (image_levels[0] - self.image_min) / image_range, (
                        image_levels[1] - self.image_min) / image_range
        logger.debug('setting bar levels to %g,%g', *bar_levels)
        self.bar.setLevels(bar_levels)

    def updateManual(self):
        if self.manual_levels is None or self.manual_lut is None:
            return
        self.vb.setYRange(*self.manual_levels, padding=0)
        self.bar.setRect(QtCore.QRectF(0, self.manual_levels[0], 1, self.manual_levels[1] - self.manual_levels[0]))
        self.bar.setLookupTable(self.manual_lut)

    def setManual(self, lut=None, levels=None):
        self.manual_levels = levels
        self.manual_lut = lut
        self.updateManual()

    def axis_to_levels(self):
        logger.debug('axis_to_levels: axis.range=%g,%g', *self.axis.range)
        for image in self.images:
            if image.levels is None:
                continue
            # If new levels significantly different from old ones (use atol=0
            # to only get relative comparison), adjust image.
            if not np.allclose(image.levels, self.axis.range, atol=0):
                image.setLevels(self.axis.range)
