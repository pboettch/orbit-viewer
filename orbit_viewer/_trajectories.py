from typing import List, Tuple
from dataclasses import dataclass, field

import datetime as dt

from astropy.units import km
from astropy.units.quantity import Quantity

import PySide2.QtCore as QtCore

from orbit_viewer.orbit_loader import OrbitLoader

import spwc

import broni

# TODO if interval A has been selected (in list 's') and range is changed so that A is out-of-range we keep it in
# the list of selected intervals to have it still selected if we are coming back to this range.
# If the interval does not exists anymore (due to filter-changes) the selection is still true
# -> needs some housekeeping

@dataclass
class _TrajectoryData:
    loader: OrbitLoader
    traj: broni.Trajectory
    all: List[Tuple[dt.datetime, dt.datetime]]
    selected: List[Tuple[dt.datetime, dt.datetime]]


class Trajectories(QtCore.QObject):
    """ Model containing all trajectories and intersection/filtering objects """

    intervals_changed = QtCore.Signal(str)
    selection_changed = QtCore.Signal(str)
    trajectory_removed = QtCore.Signal(str)

    loading_error = QtCore.Signal(str, str)
    loading_status = QtCore.Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._coord_sys = 'gse'

        self._range = (dt.datetime.now(), dt.datetime.now())
        self._intersect_objects = []

        self._data = {}
        self._detached_loaders = []  # manual garbage collection for "running threads"

    def select_interval(self, product: str, interval: Tuple[dt.datetime, dt.datetime]):
        if interval in self._data[product].all and interval not in self._data[product].selected:
            self._data[product].selected.add(interval)
            self.selection_changed.emit(product)

    def deselect_all_intervals(self):
        for product, intervals in self._data.items():
            if len(intervals.selected) > 0:
                intervals.selected = set()
                self.selection_changed.emit(product)

    def deselect_interval(self, product: str, interval: Tuple[dt.datetime, dt.datetime]):
        if interval in self._data[product].selected:
            self._data[product].selected.remove(interval)
            self.selection_changed.emit(product)

    def intervals(self, product: str):
        return self._data[product].all

    def selected_intervals(self, product: str):
        return self._data[product].selected

    def interval_from_date(self, product: str, date: dt.datetime):
        for interval in self._data[product].all:
            if interval[0] <= date <= interval[1]:
                return interval
        return None

    def set_intersect_objects(self, *args):
        self._intersect_objects = args

    def _loading_done(self, product: str, sv: spwc.SpwcVariable):
        print('orbit_loading done for', product, 'with', sv)

        # workaround - when data comes from the cache, it doesn't have the unit set
        unit = km
        if type(sv.data) is Quantity:
            unit = 1

        self._data[product].traj = broni.Trajectory(sv.values[::2, 0] * unit,
                                                    sv.values[::2, 1] * unit,
                                                    sv.values[::2, 2] * unit,
                                                    sv.time[::2],
                                                    coordinate_system=self._coord_sys)

        # reset all intervals, but not the selected ones
        self._data[product].all = broni.intervals(self._data[product].traj, self._intersect_objects)
        self.intervals_changed.emit(product)

    def _loading_error(self, product: str, msg: str):
        print('orbit_loading error for', product, 'with', msg)
        self.loading_error.emit(product, msg)

    def _loading_status(self, product: str, status: str):
        print('orbit_loading status for', product, status)
        self.loading_status.emit(product, status)

    def add(self, product):
        if product in self._data:
            raise KeyError(f'Trajectory {product} already existing - not added')

        loader = OrbitLoader(product)
        loader.status.connect(self._loading_status)
        loader.done.connect(self._loading_done)
        loader.error.connect(self._loading_error)

        self._data[product] = _TrajectoryData(loader, None, set(), set())

        loader.get_orbit(*self._range)

        self.intervals_changed.emit(product)

    def remove(self, product: str):
        if product not in self._data:
            raise KeyError(f'Trajectory {product} not existing - not removed')

        loader = self._data.pop(product).loader
        loader.done.disconnect()
        loader.error.disconnect()
        loader.status.disconnect()
        loader.quit()

        if not loader.isFinished():
            self._detached_loaders.append(loader)

        self.trajectory_removed.emit(product)

    def clean_loaders(self):
        """ clean exiting of threads """

        for t in self._detached_loaders:
            t.wait()

        for t in self._data.values():
            t.loader.quit()

        for t in self._data.values():
            t.loader.wait()

    def set_range(self, start: dt.datetime, stop: dt.datetime):
        for t in self._data.values():
            t.loader.get_orbit(start, stop)
        self._range = (start, stop)

    def names(self):
        return [str(name) for name in self._data.keys()]
