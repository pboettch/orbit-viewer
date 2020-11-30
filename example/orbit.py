#!/usr/bin/env python3

# from broni.shapes.primitives import Cuboid
# from broni.shapes.callback import SphericalBoundary, Sheath
# import broni
#
# from astropy.units import km
# from astropy.constants import R_earth
#
# import datetime
# import matplotlib.pyplot as plt
#
# import numpy as np
#
# from space.models.planetary import formisano1979, mp_formisano1979, bs_formisano1979

import sys

from typing import List

from PySide2.QtWidgets import (
    QApplication,
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QLineEdit,
    QLabel,
    QSizePolicy,
)

from PySide2.QtGui import QVector3D, QFont, QQuaternion

from PySide2.QtDataVisualization import QtDataVisualization as QtDV

from PySide2.QtCore import Signal, Qt, Slot, QSize


class _BaseWidget(QWidget):
    updated = Signal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._enabled = QCheckBox("Enabled")
        self._enabled.setCheckState(Qt.CheckState.Checked)
        self._enabled.stateChanged.connect(self._updated)

        self._layout = QVBoxLayout()
        self._layout.addWidget(self._enabled)

        self.setLayout(self._layout)

    @Slot()
    def _updated(self):
        self.updated.emit()

    @property
    def enabled(self):
        return self._enabled.isChecked()

    def _add_labeled_edit(self, value: float, label: str):
        edit = QLineEdit(str(value))
        edit.textChanged.connect(self._updated)

        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel(label))
        hlayout.addWidget(edit)
        self._layout.addLayout(hlayout)

        return edit

    def _add_labeled_edit_3(self, x, y, z: float, label: str):
        a = QLineEdit(str(x))
        a.textChanged.connect(self._updated)

        b = QLineEdit(str(y))
        b.textChanged.connect(self._updated)

        c = QLineEdit(str(z))
        c.textChanged.connect(self._updated)

        hlayout = QHBoxLayout()
        hlayout.addWidget(QLabel(label))
        hlayout.addWidget(a)
        hlayout.addWidget(b)
        hlayout.addWidget(c)
        self._layout.addLayout(hlayout)

        return a, b, c


class SphereWidget(_BaseWidget):
    def __init__(self, x: float, y: float, z: float, d: float, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._d = self._add_labeled_edit(d, "Diameter")
        self._x, self._y, self._z = self._add_labeled_edit_3(x, y, z, "Center")


class CuboidWidget(_BaseWidget):

    def __init__(self, x: float, y: float, z: float, w: float, h: float, d: float, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._x, self._y, self._z = self._add_labeled_edit_3(x, y, z, "P0")

        self._w = self._add_labeled_edit(w, "Width (X)")
        self._h = self._add_labeled_edit(h, "Height (Y)")
        self._d = self._add_labeled_edit(d, "Depth (Z)")


class Form(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle("My Form")

        # Create layout and add widgets
        layout = QVBoxLayout()
        s = SphereWidget(10, 20, 30, 100)
        s.updated.connect(self.updated)
        layout.addWidget(s)
        s = SphereWidget(100, 120, 130, 200)
        s.updated.connect(self.updated)
        layout.addWidget(s)

        s = CuboidWidget(10, 10, 20, 300, 400, 500)
        s.updated.connect(self.updated)
        layout.addWidget(s)


        surface = QtDV.Q3DScatter()
        surface.setFlags(surface.flags() ^ Qt.FramelessWindowHint)
        surface.activeTheme().setType(QtDV.Q3DTheme.ThemeQt)

        surface.setShadowQuality(QtDV.QAbstract3DGraph.ShadowQualityNone)
        surface.scene().activeCamera().setCameraPreset(QtDV.Q3DCamera.CameraPresetFront)

        surface.setOrthoProjection(True)
        surface.activeTheme().setBackgroundEnabled(False)

        surface.scene().activeCamera().setMaxZoomLevel(200.0)

        surface.axisX().setRange(0.0, 1000.0)
        surface.axisY().setRange(-600.0, 600.0)
        surface.axisZ().setRange(0.0, 1000.0)
        surface.axisX().setSegmentCount(5)
        surface.axisY().setSegmentCount(6)
        surface.axisZ().setSegmentCount(5)
        #        // Only allow zooming at the center and limit the zoom to 200% to avoid clipping issues
#        static_cast<Q3DInputHandler *>(m_graph->activeInputHandler())->setZoomAtTargetEnabled(false);


        dataRow1 = [QVector3D(0.0, 0.1, 0.5), QVector3D(1.0, 0.5, 0.5)]
        dataRow2 = [QVector3D(0.0, 1.8, 1.0), QVector3D(1.0, 1.2, 1.0)]
        data = [dataRow1, dataRow2]

        series = QtDV.QSurface3DSeries()
        print("hello")
        series.dataProxy().resetArray(data)
        surface.addSeries(series)

        warningLabel = QtDV.QCustom3DLabel(
            "QCustom3DVolume is not supported with OpenGL ES2",
            QFont(),
            QVector3D(0.0, 0.5, 0.0),
            QVector3D(1.5, 1.5, 0.0),
            QQuaternion())
        warningLabel.setPositionAbsolute(True)
        warningLabel.setFacingCamera(True)
        surface.addCustomItem(warningLabel)

        self.surface = surface
        container = QWidget.createWindowContainer(surface)

        screenSize = surface.screen().size()

        container.setMinimumSize(QSize(screenSize.width() / 3, screenSize.height() / 3))
        container.setMaximumSize(screenSize)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container.setFocusPolicy(Qt.StrongFocus)

        hlayout = QHBoxLayout(self)
        hlayout.addWidget(container, 1)
        hlayout.addLayout(layout)


    @Slot()
    def updated(self):
        print('something has been updated')


class Toto(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.graph = QtDV.Q3DBars()
        self.graph.setFlags(self.graph.flags() ^ Qt.FramelessWindowHint)

        self.graph.rowAxis().setRange(0, 4)
        self.graph.columnAxis().setRange(0, 4)

        # Make some random data points
        # dataSeries = [(i+1, randint(0, 99999)) for i in range(200)]

        series = QtDV.QBar3DSeries()
        d = [QtDV.QBarDataItem(v) for v in [1.0, 7.5, 5.0, 2.2]]

        series.dataProxy().addRows([d])
        self.graph.addSeries(series)

        container = QWidget.createWindowContainer(self.graph)
        screenSize = self.graph.screen().size()
        container.setMinimumSize(QSize(screenSize.width() / 3, screenSize.height() / 3))
        container.setMaximumSize(screenSize)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        container.setFocusPolicy(Qt.StrongFocus)

        l = QVBoxLayout()
        l.addWidget(QLineEdit("hello"))

        layout = QHBoxLayout(self)
        layout.addWidget(container, 1)
        layout.addLayout(l)



if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)
    # Create and show the form
    form = Form()
    form.show()

    # toto = Toto()
    # toto.show()

    """
    bars = QtDV.Q3DBars()
    bars.setFlags(bars.flags() ^ Qt.FramelessWindowHint)

    bars.rowAxis().setRange(0, 4)
    bars.columnAxis().setRange(0, 4)

    # Make some random data points
    # dataSeries = [(i+1, randint(0, 99999)) for i in range(200)]

    series = QtDV.QBar3DSeries()
    d = [QtDV.QBarDataItem(v) for v in [1.0, 7.5, 5.0, 2.2]]

    series.dataProxy().addRows([d])
    bars.addSeries(series)

    container = QWidget.createWindowContainer(bars)
    screenSize = bars.screen().size()
    container.setMinimumSize(QSize(screenSize.width() / 3, screenSize.height() / 3))
    container.setMaximumSize(screenSize)
    container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    container.setFocusPolicy(Qt.StrongFocus)

    l = QVBoxLayout()
    l.addWidget(QLineEdit("hello"))

    w = QDialog()

    layout = QHBoxLayout(w)
    layout.addWidget(container, 1)
    layout.addLayout(l)

    w.show()
    """

    # Run the main Qt loop
    sys.exit(app.exec_())

"""

import sys




from PySide2.QtWidgets import QApplication, QWidget, QVBoxLayout, QSlider, QPushButton, QLabel
from PySide2.QtCore import Qt, Slot

from PySide2.QtDataVisualization import QtDataVisualization

from PySide2 import QtGui
from PySide2.QtCharts import QtCharts
from PySide2.QtGui import QPainter

from PySide2.QtDataVisualization import QtDataVisualization

from random import randint


if __name__ == '__main__':
    app = QApplication([])
#    window = QWidget()
#    layout = QVBoxLayout()

    # Initialize chart
#    chart = QtCharts.QChart()

#    lineSeries = QtCharts.QLineSeries()

    bars = QtDataVisualization.Q3DBars()
    bars.setFlags(bars.flags() ^ Qt.FramelessWindowHint)

    bars.rowAxis().setRange(0, 4)
    bars.columnAxis().setRange(0, 4)

    # Make some random data points
    # dataSeries = [(i+1, randint(0, 99999)) for i in range(200)]

    series = QtDataVisualization.QBar3DSeries()
    d = [QtDataVisualization.QBarDataItem(v) for v in [1.0, 7.5, 5.0, 2.2]]

    print(series.dataProxy().addRow([d]))

    # series.dataProxy().addRow(d)
    bars.addSeries(series)

    bars.show()

#    layout.addWidget(bars)
#    window.setLayout(layout)

#    window.show()
#    window.resize(1500, 1000)

    sys.exit(app.exec_())

@Slot() # slot decorator
def youClicked():
    label.setText("You clicked the button")

@Slot() #slot decorator
def sliderValue(val):
    label.setText('Slider Value: ' + str(val))


    # coord_sys = "gse"

    # X = np.arange(-200000, 200000, 10).flatten() * km

    app = QApplication([])
    window = QWidget()
    layout = QVBoxLayout()  # Define slider widget, note the orientation argument:
    slider = QSlider(Qt.Horizontal)
    slider.valueChanged.connect(sliderValue)

    button = QPushButton("I'm just a Button man")

    label = QLabel('¯\_(ツ)_/¯')
    button.clicked.connect(youClicked)  # clicked signal

    layout.addWidget(label)
    layout.addWidget(button)
    layout.addWidget(slider) # Add the slider
    window.setLayout(layout)
    window.show()
    sys.exit(app.exec_())

"""
