#!/usr/bin/env python3

import sys

import functools

import datetime as dt

import PySide2.QtWidgets as QtWidgets
import PySide2.QtCore as QtCore

from orbit_viewer.views.timeline import Timelines
from orbit_viewer import trajectories

from broni.shapes.primitives import Cuboid, Sphere

from astropy.units import km


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    start, stop = dt.datetime.now() - dt.timedelta(days=10), dt.datetime.now()
    start, stop = dt.datetime(2021, 3, 2), dt.datetime(2021, 3, 11)

    trajectories.set_range(start, stop)
    trajectories.set_intersect_objects(Sphere(30000 * km, -30000 * km, 30000 * km, 20000 * km))

    tl = Timelines(start, stop)
    tl.setMaximumHeight(250)
    widget = QtWidgets.QWidget()

    vLayout = QtWidgets.QVBoxLayout()
    vLayout.setAlignment(QtCore.Qt.AlignTop)

    tl.range_changed.connect(trajectories.set_range)  # when range is changed in timeline update state

    def timelineCbState(product, state: int):
        if state == 2:
            trajectories.add(product)
        else:
            print('remove', product)
            trajectories.remove(product)


    def create(product):
        cb = QtWidgets.QCheckBox(widget)
        cb.setChecked(False)
        cb.setText(f"Timeline {product}")
        cb.stateChanged.connect(functools.partial(timelineCbState, product))
        vLayout.addWidget(cb)


    for product in ['mms1', 'mms2', 'not_existing']:
        create(product)

    hLayout = QtWidgets.QHBoxLayout(widget)
    hLayout.addWidget(tl, 1)
    hLayout.addLayout(vLayout)

    window = QtWidgets.QMainWindow()
    window.setCentralWidget(widget)
    window.resize(2000, 300)
    window.show()

    app.aboutToQuit.connect(trajectories.clean_loaders)

    sys.exit(app.exec_())
