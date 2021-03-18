#!/usr/bin/env python3

import pytest

import time

import PySide2.QtCore as QtCore

from orbit_viewer import trajectories
from broni.shapes.primitives import Sphere

import datetime as dt

from astropy.units import km

@pytest.fixture(scope="function")
def mock():
    class Mock(QtCore.QObject):
        error_signal = QtCore.Signal()
        ok_signal = QtCore.Signal()

        def __init__(self):
            super().__init__()
            self.i_changed = []
            self.t_removed = []
            self.s_changed = []
            self.status = []
            self.errors = []

            self.mms_1_range_3_intvs = (dt.datetime(2021, 3, 2), dt.datetime(2021, 3, 11))
            self.intersect_obj = Sphere(30000 * km, -30000 * km, 30000 * km, 20000 * km)

            trajectories.intervals_changed.connect(lambda x: self.i_changed.append(x))
            trajectories.trajectory_removed.connect(lambda x: self.t_removed.append(x))
            trajectories.selection_changed.connect(lambda x: self.s_changed.append(x))

            trajectories.loading_error.connect(lambda p, e: self.errors.append((p, e)))
            trajectories.loading_status.connect(lambda p, m: self.status.append((p, m)))

            trajectories.loading_error.connect(lambda p, e: self.error_signal.emit())
            trajectories.intervals_changed.connect(lambda x: self.ok_signal.emit())

    mock = Mock()

    trajectories._data = {}

    yield mock

    trajectories.clean_loaders()


def _check_lengths(mock, i=0, r=0, s=0, iv=0, e=0, st=0):
    assert len(mock.i_changed) == i
    assert len(mock.t_removed) == r
    assert len(mock.s_changed) == s

    assert len(trajectories._data) == iv

    assert len(mock.errors) == e
    assert len(mock.status) == st


def test_do_nothing(qtbot, mock):
    _check_lengths(mock)


def test_no_traj_get_intervals(qtbot, mock):
    with pytest.raises(KeyError):
        trajectories.intervals('test')

    with pytest.raises(KeyError):
        trajectories.selected_intervals('test')

    _check_lengths(mock)


def test_add_one_traj_no_intervals(qtbot, mock):
    with qtbot.waitSignal(mock.error_signal, timeout=5000):
        trajectories.add('test')

    _check_lengths(mock, i=1, iv=1, e=1, st=2)


def test_add_and_remove_one_traj_no_intervals(qtbot, mock):
    with qtbot.waitSignal(mock.error_signal, timeout=5000):
        trajectories.add('test')

    trajectories.remove('test')

    _check_lengths(mock, i=1, r=1, e=1, st=2)


def test_add_one_traj_3_intervals(qtbot, mock):
    with qtbot.waitSignal(mock.ok_signal, timeout=5000):
        trajectories.add('mms1')

    with qtbot.waitSignal(mock.ok_signal, timeout=5000):
        trajectories.set_range(*mock.mms_1_range_3_intvs)

    with qtbot.waitSignal(mock.ok_signal, timeout=5000):
        trajectories.set_intersect_objects(mock.intersect_obj)

    assert len(trajectories.intervals('mms1')) == 3
    assert len(trajectories.selected_intervals('mms1')) == 3

    _check_lengths(mock, i=3, iv=1, )


#def test_add_one_traj_3_intervals_select_1(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.select('test', (1, 2))
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.selected_intervals('test')) == 1
#
#    _check_lengths(mock, 1, 0, 1, 1)
#
#
#def test_add_one_traj_3_intervals_select_2(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.select('test', (1, 2))
#    intervals.select('test', (3, 4))
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.selected_intervals('test')) == 2
#
#    _check_lengths(mock, 1, 0, 2, 1)
#
#
#def test_add_one_traj_3_intervals_select_3_one_not_existing(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.select('test', (1, 2))
#    intervals.select('test', (3, 4))
#    intervals.select('test', (7, 8))
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.selected_intervals('test')) == 2
#
#    _check_lengths(mock, 1, 0, 2, 1)
#
#
#def test_add_one_traj_3_intervals_select_2_times_the_same(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.select('test', (1, 2))
#    intervals.select('test', (1, 2))
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.selected_intervals('test')) == 1
#
#    _check_lengths(mock, 1, 0, 1, 1)
#
#
#def test_add_one_traj_3_intervals_select_2_deselect_all(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.select('test', (1, 2))
#    intervals.select('test', (3, 4))
#    intervals.deselect_all()
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.selected_intervals('test')) == 0
#
#    _check_lengths(mock, 1, 0, 3, 1)
#
#
#def test_add_one_traj_3_intervals_select_2_deselect_one_by_one(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.select('test', (1, 2))
#    intervals.select('test', (3, 4))
#    intervals.deselect('test', (1, 2))
#    intervals.deselect('test', (3, 4))
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.selected_intervals('test')) == 0
#
#    _check_lengths(mock, 1, 0, 4, 1)
#
#
#def test_add_one_traj_3_intervals_1_select_deselect_1_reselect(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.select('test', (1, 2))
#    intervals.deselect('test', (1, 2))
#    intervals.select('test', (1, 2))
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.selected_intervals('test')) == 1
#
#    _check_lengths(mock, 1, 0, 3, 1)
#
#
#def test_add_two_traj_3_intervals_multiple_select_deselect(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.update_intervals('test2', [(7, 8), (9, 10), (5, 6)])
#
#    intervals.select('test', (1, 2))
#    assert len(mock.s_changed) == 1
#
#    intervals.deselect('test', (1, 2))
#    assert len(mock.s_changed) == 2
#
#    intervals.select('test', (1, 2))
#    assert len(mock.s_changed) == 3
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.intervals('test2')) == 3
#    assert len(intervals.selected_intervals('test')) == 1
#    assert len(intervals.selected_intervals('test2')) == 0
#
#    intervals.select('test2', (7, 8))
#    assert len(intervals.selected_intervals('test')) == 1
#    assert len(intervals.selected_intervals('test2')) == 1
#    assert len(mock.s_changed) == 4
#
#    intervals.deselect_all()  # emits two selection_changed signals
#    assert mock.s_changed[-2] == 'test'
#    assert mock.s_changed[-1] == 'test2'
#    assert len(mock.s_changed) == 6
#    intervals.select('test2', (7, 8))
#
#    assert len(intervals.intervals('test')) == 3
#    assert len(intervals.intervals('test2')) == 3
#    assert len(intervals.selected_intervals('test')) == 0
#    assert len(intervals.selected_intervals('test2')) == 1
#
#    _check_lengths(mock, 2, 0, 7, 2)
#
#
#def test_add_two_traj_3_same_intervals_select_deselect(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    intervals.update_intervals('test2', [(1, 2), (3, 4), (5, 6)])
#
#    intervals.select('test', (1, 2))
#    assert len(mock.s_changed) == 1
#    assert len(intervals.selected_intervals('test')) == 1
#    assert len(intervals.selected_intervals('test2')) == 0
#
#    _check_lengths(mock, 2, 0, 1, 2)
#
#
#def test_add_one_traj_3_intervals_select_change_intervals_still_selectioned(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#
#    intervals.select('test', (1, 2))
#    assert len(mock.s_changed) == 1
#    assert len(intervals.selected_intervals('test')) == 1
#
#    intervals.update_intervals('test', [(3, 4), (5, 6)])
#    assert len(mock.s_changed) == 1
#    assert len(intervals.selected_intervals('test')) == 1  # still selected
#
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#    assert len(mock.s_changed) == 1
#    assert len(intervals.selected_intervals('test')) == 1  # still selected
#
#    intervals.remove_trajectory('test')
#    assert len(mock.s_changed) == 1
#    with pytest.raises(KeyError):
#        intervals.intervals('test')
#
#    _check_lengths(mock, 3, 1, 1, 0)


#def test_one_trajectory_get_names(qtbot, mock):
#    trajectories.add('a')
#    trajectories.add('d')
#    trajectories.add('c')
#    trajectories.add('b')
#
#    assert trajectories.names() == ['a', 'd', 'c', 'b']
#
#    _check_lengths(mock, 4, 0, 0, 4)


# def test_one_trajectory_get_interval_from_date(mock):
#    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
#
#    assert intervals.interval_from_date('test', 2) == (1, 2)
#    assert intervals.interval_from_date('test', 2.5) is None
#    with pytest.raises(KeyError):
#        intervals.interval_from_date('test2', 2)
#
#    _check_lengths(mock, 1, 0, 0, 1)
#
