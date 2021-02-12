import PySide2.QtCore as QtCore

import datetime as dt

from typing import List, Tuple

from dataclasses import dataclass, field

# TODO if interval A has been selected (in list 's') and range is changed so that A is out-of-range we keep it in
# the list of selected intervals to have it still selected if we are coming back to this range.
# If the interval does not exists anymore (due to filter-changes) the selection is still true
# -> needs some housekeeping


@dataclass
class _IntervalsData:
    all: List[Tuple[dt.datetime, dt.datetime]] = field(default_factory=set)
    selected: List[Tuple[dt.datetime, dt.datetime]] = field(default_factory=set)


class Intervals(QtCore.QObject):
    """ Model containing all intervals of all trajectories """

    intervals_changed = QtCore.Signal(str)
    trajectory_deleted = QtCore.Signal(str)
    selection_changed = QtCore.Signal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._data = {}

    def update_intervals(self, name: str, intervals: List[Tuple[dt.datetime, dt.datetime]]):
        self._data.setdefault(name, _IntervalsData())
        # resett all intervals, but not the selected ones
        self._data[name].all = set(intervals)
        self.intervals_changed.emit(name)

    def remove_trajectory(self, name: str):
        self._data.pop(name)
        self.trajectory_deleted.emit(name)

    def select(self, name: str, interval: Tuple[dt.datetime, dt.datetime]):
        if interval in self._data[name].all and \
               interval not in self._data[name].selected:
            self._data[name].selected.add(interval)
            self.selection_changed.emit(name)

    def deselect_all(self):
        for name, intervals in self._data.items():
            if len(intervals.selected) > 0:
                intervals.selected = set()
                self.selection_changed.emit(name)

    def deselect(self, name: str, interval: Tuple[dt.datetime, dt.datetime]):
        if interval in self._data[name].selected:
            self._data[name].selected.remove(interval)
            self.selection_changed.emit(name)

    def intervals(self, name: str):
        return self._data[name].all

    def selected_intervals(self, name: str):
        return self._data[name].selected

    def interval_from_date(self, name: str, date: dt.datetime):
        for interval in self._data[name].all:
            if interval[0] <= date <= interval[1]:
                return interval
        return None

    def trajectory_names(self):
        return [str(name) for name in self._data.keys()]
