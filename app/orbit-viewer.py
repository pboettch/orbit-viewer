#!/usr/bin/env python3

import sys
from typing import List, Tuple

import time
import pandas as pds

from astropy.constants import R_earth
from astropy.units import km

import datetime as dt

from PySide2.QtWidgets import (
    QApplication,
)

from PySide2 import QtCore

from PySide2.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
)
from PySide2.QtGui import (
    QColor,
    QVector3D,
)

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender

from orbit_viewer.views.timeline import TimelineWidget
from orbit_viewer.geometries.line import LineRenderer

import spwc

import broni
from broni.shapes.primitives import Sphere


class OrbitLoadWorker(QtCore.QObject):
    error = QtCore.Signal(str)
    done = QtCore.Signal(spwc.SpwcVariable)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._ssc = spwc.SscWeb()

    @QtCore.Slot(str, dt.datetime, dt.datetime)
    def get_orbit(self, product: str, start: dt.datetime, stop: dt.datetime):
        try:
            var = self._ssc.get_orbit(product=product,
                                      start_time=start,
                                      stop_time=stop,
                                      coordinate_system='gse')
            self.done.emit(var)

        except Exception as e:
            self.error.emit(e)


# could be base-classed with a Timeline-class, for the moment we only have trajectories
class Trajectory():
    def __init__(self, name: str,
                 root_entity: Qt3DCore.QEntity):

        self._name = name
        self._intervals = []
        self._range = None

        self._broni = None

        self._spwc_var = None

        self._root_entity = root_entity
        self._line_entity = Qt3DCore.QEntity(root_entity)

        material = Qt3DExtras.QPhongMaterial(self._line_entity)
        material.setAmbient(QColor('lightgreen'))
        # for t in material.effect().techniques():
        #     for rp in t.renderPasses():
        #         point_size = Qt3DRender.QPointSize(rp)
        #
        #         point_size.setSizeMode(Qt3DRender.QPointSize.SizeMode.Fixed)
        #         point_size.setValue(5.0)
        #         rp.addRenderState(point_size)
        self._line_entity.addComponent(material)
        self._line_renderer = None

        self._interval_entities = []

    def intervals(self):
        return self._intervals

    def _create_interval_line(self, x, y, z) -> Qt3DCore.QEntity:
        entity = Qt3DCore.QEntity(self._root_entity)

        material = Qt3DExtras.QPhongMaterial(entity)
        material.setAmbient(QColor('red'))
        # for t in material.effect().techniques():
        #     for rp in t.renderPasses():
        #         point_size = Qt3DRender.QPointSize(rp)

        #         point_size.setSizeMode(Qt3DRender.QPointSize.SizeMode.Fixed)
        #         point_size.setValue(5.0)
        #         rp.addRenderState(point_size)
        entity.addComponent(material)

        renderer = LineRenderer(x / R_earth.to('km').value,
                                y / R_earth.to('km').value,
                                z / R_earth.to('km').value, 0, entity)
        renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Points)
        entity.addComponent(renderer)

        return entity

    def set_intervals(self, intervals):
        self._intervals = intervals
        self._update()

    def set_range(self, range: Tuple[dt.datetime, dt.datetime]):
        self._range = range
        self._update()

    def range(self):
        return self._range[0], self._range[1]

    def _update(self):
        return None
        if self._range is None:
            return

        coord_sys = 'gse'

        self._spwc_var = self._ssc.get_orbit(product=self._name,
                                             start_time=self._range[0],
                                             stop_time=self._range[1],
                                             coordinate_system=coord_sys)

        if self._line_renderer is not None:
            self._line_entity.removeComponent(self._line_renderer)

        self._broni = broni.Trajectory(self._spwc_var.data[:, 0] / R_earth.to('km').value * km,
                                       self._spwc_var.data[:, 1] / R_earth.to('km').value * km,
                                       self._spwc_var.data[:, 2] / R_earth.to('km').value * km,
                                       pds.to_datetime(self._spwc_var.time, unit='s'),
                                       coordinate_system=coord_sys)

        self._line_renderer = LineRenderer(self._spwc_var.data[:, 0] / R_earth.to('km').value,
                                           self._spwc_var.data[:, 1] / R_earth.to('km').value,
                                           self._spwc_var.data[:, 2] / R_earth.to('km').value,
                                           0,
                                           self._line_entity)
        self._line_entity.addComponent(self._line_renderer)

        for ie in self._interval_entities:
            for c in ie.components():
                ie.removeComponent(c)

        self._interval_entities = []

        for interval in self._intervals:
            var = self._spwc_var[interval[0]:interval[1]]
            self._interval_entities.append(
                self._create_interval_line(var.data[:, 0], var.data[:, 1], var.data[:, 2])
            )

    def name(self):
        return self._name

    def broni(self):
        return self._broni


class Sphere():
    def __init__(self, root_entity: Qt3DCore.QEntity):
        self._root_entity = root_entity
        self._entity = Qt3DCore.QEntity(root_entity)

        material = Qt3DExtras.QPhongAlphaMaterial(self._entity)
        material.setAmbient(QColor('lightblue'))
        self._entity.addComponent(material)

        self._mesh = Qt3DExtras.QSphereMesh(self._entity)
        # self._mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)
        self._entity.addComponent(self._mesh)

        self._transform = Qt3DCore.QTransform(self._entity)
        self._entity.addComponent(self._transform)

    def set_position(self, translation: QVector3D):
        self._transform.setTranslation(translation)

    def set_radius(self, radius: float):
        self._mesh.setRadius(radius)

    def broni(self):
        return broni.shapes.primitives.Sphere(
            self._transform.translation().x() * km,
            self._transform.translation().y() * km,
            self._transform.translation().z() * km,
            self._mesh.radius() * km)


class OrbitViewerSession(QtCore.QObject):
    range_changed = QtCore.Signal(tuple)
    load_orbit = QtCore.Signal(str, dt.datetime, dt.datetime)

    def __init__(self, name: str, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._range = (dt.datetime.now() - dt.timedelta(days=10), dt.datetime.now())
        self._name = name

        self._loader_thread = QtCore.QThread()
        self._loader_thread.start()

        self._loader = OrbitLoadWorker()
        self._loader.moveToThread(self._loader_thread)

        self.load_orbit.connect(self._loader.get_orbit)
        self._loader.done.connect(self.load_done)
        self._loader.error.connect(self.load_error)

    def load_done(self, var: spwc.SpwcVariable):
        print('done', var)
        # self.range_changed.emit(range)

    def load_error(self, msg: str):
        print('load error', str)

    def set_range(self, range: Tuple[dt.datetime, dt.datetime]):
        print('set_range')
        if range[0] > range[1]:
            raise ValueError("start-date of range has to be before the stop-date")

        self._range = range
        # for each orbit

        self.load_orbit.emit('mms1', range[0], range[1])

    def range(self):
        return self._range

    def load(self, file):
        pass

    def save(self, file):
        pass


class SpaceView(Qt3DExtras.Qt3DWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.defaultFrameGraph().setClearColor(QColor("black"))

        self._root = Qt3DCore.QEntity()

        # Camera
        camera = self.camera()
        camera.lens().setPerspectiveProjection(65.0, 16.0 / 9.0, 0.1, 200.0)
        camera.setPosition(QVector3D(0, 50, 50.0))
        camera.setViewCenter(QVector3D(0, 0, 0))

        cam_ctrl = Qt3DExtras.QOrbitCameraController(self._root)
        cam_ctrl.setCamera(camera)

        self.light_entity = Qt3DCore.QEntity(camera)  # light follows camera source
        light = Qt3DRender.QPointLight(self.light_entity)
        light.setColor("white")
        light.setIntensity(100)
        self.light_entity.addComponent(light)

        self.setRootEntity(self._root)

    def root_entity(self):
        return self._root


class AWidget(QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._trajectories = []

        self.state = OrbitViewerSession('default')

        self.sc = TimelineWidget(self.state.range())
        self.sc.setMaximumHeight(250)
        self.sc.range_changed.connect(self.state.set_range)  # when range is changed in timeline update state

        self.state.range_changed.connect(self.timeline_range_changed)

        self.view = SpaceView()
        container = QWidget.createWindowContainer(self.view)
        container.setMinimumSize(QtCore.QSize(800, 800))

        tl = Trajectory("mms1", self.view.root_entity())
        tl.set_range(self.state.range())
        self.sc.add_timeline(tl)
        self._trajectories.append(tl)

        self.sphere = Sphere(self.view.root_entity())
        self.sphere.set_position(QVector3D(10, 24, 0))
        self.sphere.set_radius(4)

        layout = QVBoxLayout(self)
        self.setLayout(layout)
        layout.addWidget(self.sc)
        layout.addWidget(container)

    def timeline_range_changed(self, time_range: Tuple):
        traj = self._trajectories[0]

        traj.set_range(time_range)

        intervals = broni.intervals(traj.broni(), [self.sphere.broni()])
        print(intervals)
        traj.set_intervals(intervals)
        self.sc.interval_updated()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    main = QMainWindow()

    w = AWidget(main)
    main.setCentralWidget(w)
    main.show()

    sys.exit(app.exec_())
