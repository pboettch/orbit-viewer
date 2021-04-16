#!/usr/bin/env python3

import sys
from typing import List, Tuple

import datetime as dt

from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

from orbit_viewer.views.timeline import Timelines
from orbit_viewer.views.spaceview import SpaceView
from orbit_viewer.views.entities import EntitiesWidget
from orbit_viewer.entities import Entities, Trajectory, Axis, Sphere

from orbit_viewer import trajectories

from astropy.constants import R_earth


class OrbitViewer(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.tl = Timelines(dt.datetime(2021, 3, 2), dt.datetime(2021, 3, 11))
        self.tl.setMaximumHeight(250)
        self.tl.range_changed.connect(trajectories.set_range)  # when range is changed in timeline update state

        trajectories.set_range(*self.tl.range())

        self.view = SpaceView()
        container = QtWidgets.QWidget.createWindowContainer(self.view)
        container.setMinimumSize(QtCore.QSize(800, 800))

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tl)
        layout.addWidget(container)

        h_layout = QtWidgets.QHBoxLayout(self)

        self.entities = Entities(self)

        earth = Sphere('Earth', self.view.scene(), self.view.middle_layer(), self)
        earth.set('Radius', R_earth.to('Mm').value)
        earth.set('Color', QtGui.QColor.fromRgb(43, 206, 255))
        self.entities.add_fix_object(earth)

        x_axis = Axis('X-axis', QtGui.QVector3D(1, 0, 0), self.view.scene(), self.view.lower_layer(), self)
        x_axis.set('Color', QtGui.QColor.fromRgb(255, 0, 0))
        self.entities.add_fix_object(x_axis)
        y_axis = Axis('Y-axis', QtGui.QVector3D(0, 1, 0), self.view.scene(), self.view.lower_layer(), self)
        y_axis.set('Color', QtGui.QColor.fromRgb(0, 255, 0))
        self.entities.add_fix_object(y_axis)
        z_axis = Axis('Z-axis', QtGui.QVector3D(0, 0, 1), self.view.scene(), self.view.lower_layer(), self)
        z_axis.set('Color', QtGui.QColor.fromRgb(170, 255, 255))
        self.entities.add_fix_object(z_axis)

        ent_widget = EntitiesWidget(self.entities, self.view, self)
        ent_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        h_layout.addWidget(ent_widget, alignment=QtCore.Qt.AlignTop)
        h_layout.addLayout(layout)

        self.setLayout(layout)

    def set_trajectories(self, trajs: List[str]):
        for product in trajs:
            self.entities.add_trajectory(Trajectory(product, self.view.scene(), self.view.lower_layer(), self))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    main = QtWidgets.QMainWindow()

    w = OrbitViewer(main)
    w.set_trajectories(['mms1', 'cluster1'])

    main.setCentralWidget(w)

    main.show()

    app.aboutToQuit.connect(trajectories.clean_loaders)

    sys.exit(app.exec_())
