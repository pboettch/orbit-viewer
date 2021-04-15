import functools

from ..entities import Entities, Sphere, Cuboid, SphericalBoundary, Sheath, Trajectory
from ..properties.properties import PropertyHolder
from .properties import PropertyEditorWidget
from .spaceview import SpaceView

from PySide2 import QtWidgets
from PySide2 import QtCore


class EntitiesWidget(QtWidgets.QWidget):
    def __init__(self, entities: Entities, view: SpaceView, parent=None):
        super().__init__(parent)

        self._entities = entities

        self._tv = QtWidgets.QTreeView(self)
        self._tv.setMinimumWidth(300)
        self._tv.setMaximumWidth(300)
        self._tv.setMinimumHeight(300)
        self._tv.setHeaderHidden(True)
        self._tv.setModel(self._entities.model())
        self._tv.setSelectionMode(QtWidgets.QTreeView.SingleSelection)

        self._tv.selectionModel().currentChanged.connect(self.item_activated)
        self._tv.model().rowsInserted.connect(
            lambda parent, first, last: self._tv.expand(parent) if not self._tv.isExpanded(parent) else None)

        self._current_pro_widget = None

        toolbar = QtWidgets.QToolBar(self)

        menu = QtWidgets.QMenu(self)

        submenu = menu.addMenu('Intersection')

        for cl, name, layer in [(Sphere, 'Sphere', view.middle_layer()),
                                (Cuboid, 'Cuboid', view.middle_layer()),
                                (SphericalBoundary, 'SphericalBoundary', view.higher_layer()),
                                (Sheath, 'Sheath', view.higher_layer())]:
            action = QtWidgets.QAction(name, self)
            action.triggered.connect(
                functools.partial(
                    lambda _class, _name, _layer: self._entities.add_intersection(
                        _class('New ' + _name,
                               view.scene(),
                               _layer,
                               self)),
                    cl,
                    name,
                    layer))

            submenu.addAction(action)

        submenu = menu.addMenu('Trajectories')

        # TODO get products from spwc
        for product in ['mms1', 'mms2', 'cluster1', 'cluster2']:
            action = QtWidgets.QAction(product, self)
            action.setEnabled(False)
            # action.triggered.connect(
            #     functools.partial(
            #         lambda _product: self._entities.trajectories().appendRow(Trajectory(_product,
            #                                                                             view.scene(),
            #                                                                             view.lower_layer(),
            #                                                                             self)),
            #         product))

            submenu.addAction(action)

        tbb = QtWidgets.QToolButton(self)
        tbb.setText('Add')
        tbb.setMenu(menu)
        tbb.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        toolbar.addWidget(tbb)

        self._remove_button = QtWidgets.QToolButton(self)
        self._remove_button.setText('Remove')
        self._remove_button.setEnabled(False)
        self._remove_button.clicked.connect(self.remove_item)

        toolbar.addWidget(self._remove_button)

        v_layout = QtWidgets.QVBoxLayout(self)
        v_layout.setMenuBar(toolbar)
        v_layout.addWidget(self._tv)

        self.setLayout(v_layout)

    def item_activated(self, index: QtCore.QModelIndex, previous: QtCore.QModelIndex):
        if index.parent() in [self._entities.intersection_entities_index()]:
            #, self._entities.trajectories().index()]:
            self._remove_button.setEnabled(True)
        else:
            self._remove_button.setEnabled(False)

        if self._current_pro_widget:
            self.layout().removeWidget(self._current_pro_widget)
            self._current_pro_widget.deleteLater()
            self._current_pro_widget = None

        item = self._entities.model().itemFromIndex(index)

        if issubclass(type(item), PropertyHolder):
            self._current_pro_widget = PropertyEditorWidget(item)
            self.layout().addWidget(self._current_pro_widget)

    def remove_item(self):
        index = self._tv.currentIndex()
        if index.isValid():

            # TODO delete item from entities
            self._tv.model().removeRow(index.row(), index.parent())
            self._tv.selectionModel().setCurrentIndex(index.parent(),
                                                      QtCore.QItemSelectionModel.Select)

