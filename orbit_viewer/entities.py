from .properties import PropertyHolder, Property

from math import pi

import random

import numpy as np

from typing import Callable

from PySide2 import QtCore
from PySide2 import QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DExtras import Qt3DExtras

from astropy.constants import R_earth
from astropy.units import km
import space.models.planetary

from orbit_viewer.geometries.line import LineRenderer
from orbit_viewer.geometries.callback import SphericalModelRenderer
from orbit_viewer import trajectories

import broni.shapes.primitives
import broni.shapes.callback


class IntersectionObjectPropertyHolder(QtGui.QStandardItem, PropertyHolder):
    geometry_changed = QtCore.Signal()

    def __init__(self, name: str, root: Qt3DCore.QEntity, alpha_layers: Callable[[int], Qt3DRender.QLayer],
                 parent=None):
        QtGui.QStandardItem.__init__(self, name)
        PropertyHolder.__init__(self, parent)

        self._entity = Qt3DCore.QEntity(root)

        color_list = [name for name in QtGui.QColor.colorNames() if 'light' in name]
        # color_list.remove('black')
        color = color_list[random.randint(0, len(color_list) - 1)]

        self._name = self.add_property('Name', "Object name", str, name, read_only=True)
        self._visible = self.add_property('Visible', 'Visibility of object in 3DView', bool, True)
        self._enabled = self.add_property('Enabled', 'Object enabled for interval-intersection', bool, True)
        self._color = self.add_property('Color', 'Diffuse color', QtGui.QColor, QtGui.QColor(color), alpha=True)
        self._alpha = self.add_property('Alpha', 'Alpha value for the diffuse color', int, 255, minimum=0, maximum=255)

        # Qt3D-part
        self._material = Qt3DExtras.QDiffuseSpecularMaterial(self._entity)
        self._material.setAlphaBlendingEnabled(True)
        self._material.setDiffuse(self._color.value)
        self._entity.addComponent(self._material)

        # trying to solve the "draw-order" problem - taken from
        # https://forum.qt.io/topic/110219/depth-problem-with-qt3d/4
        for current_tech in self._material.effect().techniques():
            #print('current_tech', current_tech)
            for render_pass in current_tech.renderPasses():
                #print('  rend_pass', render_pass)
                for render_state in render_pass.renderStates():
                    #print('    ', render_state)
                    if isinstance(render_state, Qt3DRender.QNoDepthMask):
                        render_pass.removeRenderState(render_state)
                        depth_test = Qt3DRender.QDepthTest(self._entity)
                        depth_test.setDepthFunction(Qt3DRender.QDepthTest.Less)
                        render_pass.addRenderState(depth_test)
                        break

        self._transform = Qt3DCore.QTransform(self._entity)
        self._entity.addComponent(self._transform)
        self._alpha_layers = alpha_layers

        self._current_layer = alpha_layers(self._alpha.get())
        self._entity.addComponent(self._current_layer)

        self.property_has_changed.connect(self.property_value_updated)

    def property_value_updated(self, prop: Property):
        if prop.name == 'Color':
            self._alpha.set(prop.get().alpha())
            self._material.setDiffuse(prop.value)
        elif prop.name == 'Alpha':
            color = self._color.get()
            color.setAlpha(prop.get())
            self._color.set(color)

            new_layer = self._alpha_layers(prop.get())
            if new_layer != self._current_layer:
                self._entity.removeComponent(self._current_layer)
                self._entity.addComponent(new_layer)
                self._current_layer = new_layer

        elif prop.name == 'Visible':
            if prop.value:
                self._entity.addComponent(self._material)
            else:
                self._entity.removeComponent(self._material)
        elif prop.name == 'Enabled':
            self.geometry_changed.emit()

    def setData(self, value, role):
        super().setData(value, role)

        if role == QtCore.Qt.EditRole:
            self._name.set(value)

    def name(self):
        return self._name.get()

    def enabled_for_intersecting(self):
        return self._enabled.get()

    def remove_entity_components(self):
        self._entity.parentEntity().childNodes().remove(self._entity)
        for c in self._entity.components()[:]:
            self._entity.removeComponent(c)


class Sphere(IntersectionObjectPropertyHolder):
    def __init__(self, name: str, root: Qt3DCore.QEntity, alpha_layers: Callable[[int], Qt3DRender.QLayer],
                 parent=None):
        super().__init__(name, root, alpha_layers, parent)

        self._mesh = Qt3DExtras.QSphereMesh(self._entity)
        self._entity.addComponent(self._mesh)

        self._radius = self.add_property('Radius', "The sphere's radius", float, self._mesh.radius(), minimum=0)
        self._x = self.add_property('X', "X coordinate of center", float, 0)
        self._y = self.add_property('Y', "Y coordinate of center", float, 0)
        self._z = self.add_property('Z', "Z coordinate of center", float, 0)

    def property_value_updated(self, prop: Property):
        super().property_value_updated(prop)

        if prop.name == 'Radius':
            self._mesh.setRadius(prop.value)
            self.geometry_changed.emit()
        elif prop.name in ['X', 'Y', 'Z']:
            self._transform.setTranslation(QtGui.QVector3D(self._x.get(), self._y.get(), self._z.get()))
            self.geometry_changed.emit()

    def to_broni(self):
        return broni.shapes.primitives.Sphere(
            self._transform.translation().x() * 1e3 * km,
            self._transform.translation().y() * 1e3 * km,
            self._transform.translation().z() * 1e3 * km,
            self._mesh.radius() * 1e3 * km)


class Cuboid(IntersectionObjectPropertyHolder):
    def __init__(self, name: str, root: Qt3DCore.QEntity, alpha_layers: Callable[[int], Qt3DRender.QLayer],
                 parent=None):
        super().__init__(name, root, alpha_layers, parent)

        self._mesh = Qt3DExtras.QCuboidMesh(self._entity)
        # self._mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)
        self._entity.addComponent(self._mesh)

        self._x = self.add_property('X', "X of center point", float, self._transform.translation().x())
        self._y = self.add_property('Y', "Y of center point", float, self._transform.translation().y())
        self._z = self.add_property('Z', "Z of center point", float, self._transform.translation().z())

        self._x_ext = self.add_property('X-extent', "X-Extent (width)", float, self._mesh.xExtent(), minumum=0)
        self._y_ext = self.add_property('Y-extent', "Y-Extent (height)", float, self._mesh.yExtent(), minumum=0)
        self._z_ext = self.add_property('Z-extent', "Z-Extent (depth)", float, self._mesh.zExtent(), minumum=0)

    def property_value_updated(self, prop: Property):
        super().property_value_updated(prop)

        if prop.name in ['X', 'Y', 'Z']:
            self._transform.setTranslation(QtGui.QVector3D(self._x.get(), self._y.get(), self._z.get()))
            self.geometry_changed.emit()
        elif prop.name == 'X-extent':
            self._mesh.setXExtent(prop.value)
            self.geometry_changed.emit()
        elif prop.name == 'Y-extent':
            self._mesh.setYExtent(prop.value)
            self.geometry_changed.emit()
        elif prop.name == 'Z-extent':
            self._mesh.setZExtent(prop.value)
            self.geometry_changed.emit()

    def to_broni(self):
        return broni.shapes.primitives.Cuboid(
            (self._transform.translation().x() - self._mesh.xExtent() / 2) * 1e3 * km,
            (self._transform.translation().y() - self._mesh.yExtent() / 2) * 1e3 * km,
            (self._transform.translation().z() - self._mesh.zExtent() / 2) * 1e3 * km,
            (self._transform.translation().x() + self._mesh.xExtent() / 2) * 1e3 * km,
            (self._transform.translation().y() + self._mesh.yExtent() / 2) * 1e3 * km,
            (self._transform.translation().z() + self._mesh.zExtent() / 2) * 1e3 * km
        )


class SphericalBoundary(IntersectionObjectPropertyHolder):
    def __init__(self, name: str, root: Qt3DCore.QEntity, alpha_layers: Callable[[int], Qt3DRender.QLayer],
                 parent=None):
        super().__init__(name, root, alpha_layers, parent)

        # models = []
        # for name in dir(space.models.planetary):
        #    if (name.startswith('mp_') or name.startswith('bs_')) and name.count('_') == 1:
        #        models.append(name)
        models = ['mp_formisano1979', 'bs_formisano1979']

        models.sort()

        self._model = self.add_property('Model', 'Underlying model for the sheath',
                                        models, models[0])
        self._model_function = eval('space.models.planetary.' + models[0])
        print(self._model_function)

        self._lower = self.add_property('Lower', "Lower bound", float, -1)
        self._upper = self.add_property('Upper', "Upper margin", float, 1)

        self._primitive = self.add_property('3D Primitive', "The object\'s primitive display type",
                                            ['Points', 'Lines', 'LineStrip', 'Triangles'], 'Triangles')

        self._mesh = Qt3DExtras.QCuboidMesh(self._entity)
        # self._mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)
        self._entity.addComponent(self._mesh)

        self._mesh = None
        self._refresh_mesh()

    def _refresh_mesh(self):
        if self._mesh:
            self._entity.removeComponent(self._mesh)
        self._mesh = SphericalModelRenderer(2 * pi, 0.8 * pi, self._model_function, 30, 15, self._entity)
        self._entity.addComponent(self._mesh)

    def property_value_updated(self, prop: Property):
        super().property_value_updated(prop)

        if prop.name == 'Model':
            self._model_function = eval('space.models.planetary.' + prop.get())
            self._refresh_mesh()
            self.geometry_changed.emit()
        elif prop.name == '3D Primitive':
            if prop.value == 'Triangles':
                self._mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.Triangles)
            elif prop.value == 'Points':
                self._mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.Points)
            elif prop.value == 'Lines':
                self._mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)
            elif prop.value == 'LineStrip':
                self._mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)
        elif prop.name in ['Upper', 'Lower']:
            self.geometry_changed.emit()

    def to_broni(self):
        return broni.shapes.callback.SphericalBoundary(self._model_function,
                                                       self._lower.get() * R_earth,
                                                       self._upper.get() * R_earth,
                                                       scale=R_earth)


class Sheath(IntersectionObjectPropertyHolder):
    def __init__(self, name: str, root: Qt3DCore.QEntity, alpha_layers: Callable[[int], Qt3DRender.QLayer],
                 parent=None):
        super().__init__(name, root, alpha_layers, parent)

        self._model = self.add_property('Model', 'Underlying model for the sheath', ['one', 'two'], 'one')
        self._inner = self.add_property('Inner', "Inner margin", float, 0, minumum=0)
        self._outer = self.add_property('Outer', "Outer margin", float, 0, minumum=0)


class Interval(Qt3DCore.QEntity):
    def __init__(self, root: Qt3DCore.QEntity, layer: Qt3DRender.QLayer, x, y, z):
        super().__init__(root)

        self.renderer = LineRenderer(x / 1e3, y / 1e3, z / 1e3, 0, self)
        self.renderer.setPrimitiveType(Qt3DRender.QGeometryRenderer.Points)
        self.addComponent(self.renderer)
        self.addComponent(layer)

        self.material = Qt3DExtras.QPhongMaterial(self)
        for t in self.material.effect().techniques():
            for rp in t.renderPasses():
                point_size = Qt3DRender.QPointSize(rp)

                point_size.setSizeMode(Qt3DRender.QPointSize.SizeMode.Fixed)
                point_size.setValue(5.0)
                rp.addRenderState(point_size)
        self.addComponent(self.material)

        self.set_color('red')

    def set_color(self, color: str):
        self.material.setAmbient(QtGui.QColor(color))

    def remove(self):
        self.removeComponent(self.renderer)


class Axis(IntersectionObjectPropertyHolder):
    def __init__(self, name: str, dir: QtGui.QVector3D, root: Qt3DCore.QEntity,
                 alpha_layers: Callable[[int], Qt3DRender.QLayer], parent=None):
        super().__init__(name, root, alpha_layers, parent)

        self._material.setAmbient(self._color.get())

        self._dir = dir

        self._min = self.add_property('Min', "Minimum", float, 0)
        self._max = self.add_property('Max', "Maximum", float, 20)

        self._line_renderer = None
        self.update()

    def property_value_updated(self, prop: Property):
        super().property_value_updated(prop)

        if prop.name in ['Min', 'Max']:
            self.update()

    def update(self):
        if self._line_renderer:
            self._entity.removeComponent(self._line_renderer)

        min = self._dir * self._min.get()
        max = self._dir * self._max.get()

        self._line_renderer = LineRenderer(np.asarray([min.x(), max.x()]),
                                           np.asarray([min.y(), max.y()]),
                                           np.asarray([min.z(), max.z()]), 0, self._entity)
        self._entity.addComponent(self._line_renderer)


class Trajectory(IntersectionObjectPropertyHolder):
    def __init__(self, product: str, root: Qt3DCore.QEntity, alpha_layers: Callable[[int], Qt3DRender.QLayer],
                 parent=None):
        super().__init__(product, root, alpha_layers, parent)

        self._product = product
        self._line_renderer = None
        self._intervals = {}

        self._material.setAmbient(self._color.get())

        trajectories.intervals_changed.connect(self.intervals_changed)
        trajectories.trajectory_data_changed.connect(self.trajectory_data_changed)
        trajectories.interval_selection_changed.connect(self.intervals_selection_changed)

        trajectories.add(product)

    def property_value_updated(self, prop: Property):
        super().property_value_updated(prop)

        if prop.name == 'Color':
            self._material.setAmbient(prop.get())

    def trajectory_data_changed(self, product: str):
        if self._product != product:
            return

        if self._line_renderer:
            self._entity.removeComponent(self._line_renderer)

        traj = trajectories.broni_trajectory(product)

        self._line_renderer = LineRenderer(traj.x[::2] / 1e3, traj.y[::2] / 1e3, traj.z[::2] / 1e3, 0, self._entity)
        self._entity.addComponent(self._line_renderer)

    def intervals_changed(self, product: str):
        if self._product != product:
            return

        intervals = trajectories.intervals(product)

        # remove no-more-existing intervals
        for iv in set(self._intervals.keys()) - set(intervals):
            print('rm', iv)
            self._intervals.pop(iv).remove()

        # add new intervals
        for iv in set(self._intervals.keys()) ^ set(intervals):
            print('add', iv)
            spwc = trajectories.interval_coords(self._product, iv)
            self._intervals[iv] = Interval(self._entity, self._alpha_layers(255),
                                           spwc[:, 0], spwc[:, 1], spwc[:, 2])
            if iv in trajectories.selected_intervals(self._product):
                self._intervals[iv].set_color('yellow')

    def intervals_selection_changed(self, product: str):
        if self._product != product:
            return

        intervals = trajectories.selected_intervals(product)

        for k, iv in self._intervals.items():
            if k in intervals:
                iv.set_color('yellow')
            else:
                iv.set_color('red')


class IntersectionEntities(QtGui.QStandardItem):
    """ Group of broni-interval-selection object """

    def __init__(self, name: str):
        super().__init__(name)

        self.setEditable(False)


class TrajectoryEntities(QtGui.QStandardItem):
    """ Group of trajectories """

    def __init__(self, name: str):
        super().__init__(name)

        self.setEditable(False)


class Entities(QtCore.QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = QtGui.QStandardItemModel(self)

        self._intersection_entities = IntersectionEntities('Intersections')
        self._model.invisibleRootItem().appendRow(self._intersection_entities)

        self._fix_objects_entities = IntersectionEntities('Fix objects')
        self._model.invisibleRootItem().appendRow(self._fix_objects_entities)

        self._trajectory_entities = TrajectoryEntities('Trajectories')
        self._model.invisibleRootItem().appendRow(self._trajectory_entities)

        self._model.rowsAboutToBeRemoved.connect(self.rows_about_to_be_removed)
        self._model.rowsRemoved.connect(self.rows_removed)

    def model(self):
        return self._model

    def add_intersection(self, item) -> None:
        self._intersection_entities.appendRow(item)
        self.geometry_changed()

        item.geometry_changed.connect(self.geometry_changed)

    def intersection_entities_index(self) -> QtCore.QModelIndex:
        return self._intersection_entities.index()

    def rows_about_to_be_removed(self, parent_index: QtCore.QModelIndex, first: int, last: int):
        parent = self._model.itemFromIndex(parent_index)
        if parent == self._intersection_entities:
            index = parent_index.child(first, 0)
            item = self._model.itemFromIndex(index)
            item.remove_entity_components()

    def rows_removed(self, parent_index: QtCore.QModelIndex, first: int, last: int):
        parent = self._model.itemFromIndex(parent_index)
        if parent == self._intersection_entities:
            self.geometry_changed()

    def add_fix_object(self, item) -> None:
        self._fix_objects_entities.appendRow(item)

    def add_trajectory(self, item) -> None:
        self._trajectory_entities.appendRow(item)
        self.geometry_changed()

    def geometry_changed(self) -> None:
        intsct = []
        for i in range(self._intersection_entities.rowCount()):
            item = self._intersection_entities.child(i)
            if item.enabled_for_intersecting():
                intsct += [item.to_broni()]

        # print(intsct)
        trajectories.set_intersect_objects(*intsct)
