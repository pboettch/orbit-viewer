#!/usr/bin/env python

import pytest

from orbit_viewer import intervals


@pytest.fixture(scope="function")
def mock():
    class Mock:
        def __init__(self):
            self.i_changed = []
            self.t_deleted = []
            self.s_changed = []

            intervals.intervals_changed.connect(lambda x: self.i_changed.append(x))
            intervals.trajectory_deleted.connect(lambda x: self.t_deleted.append(x))
            intervals.selection_changed.connect(lambda x: self.s_changed.append(x))

            intervals._data = {}

    return Mock()


def _check_lengths(mock, i, t, s, iv):
    assert len(mock.i_changed) == i
    assert len(mock.t_deleted) == t
    assert len(mock.s_changed) == s

    assert len(intervals._data) == iv


def test_do_nothing(mock):
    _check_lengths(mock, 0, 0, 0, 0)


def test_no_traj_get_intervals(mock):
    with pytest.raises(KeyError):
        intervals.intervals('test')

    with pytest.raises(KeyError):
        intervals.selected_intervals('test')

    _check_lengths(mock, 0, 0, 0, 0)


def test_add_one_traj_no_intervals(mock):
    intervals.update_intervals('test', [])

    _check_lengths(mock, 1, 0, 0, 1)


def test_add_and_remove_one_traj_no_intervals(mock):
    intervals.update_intervals('test', [])
    intervals.remove_trajectory('test')

    _check_lengths(mock, 1, 1, 0, 0)


def test_add_one_traj_3_intervals(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 0

    _check_lengths(mock, 1, 0, 0, 1)


def test_add_one_traj_3_intervals_select_1(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.select('test', (1, 2))

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 1

    _check_lengths(mock, 1, 0, 1, 1)


def test_add_one_traj_3_intervals_select_2(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.select('test', (1, 2))
    intervals.select('test', (3, 4))

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 2

    _check_lengths(mock, 1, 0, 2, 1)


def test_add_one_traj_3_intervals_select_3_one_not_existing(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.select('test', (1, 2))
    intervals.select('test', (3, 4))
    intervals.select('test', (7, 8))

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 2

    _check_lengths(mock, 1, 0, 2, 1)


def test_add_one_traj_3_intervals_select_2_times_the_same(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.select('test', (1, 2))
    intervals.select('test', (1, 2))

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 1

    _check_lengths(mock, 1, 0, 1, 1)


def test_add_one_traj_3_intervals_select_2_deselect_all(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.select('test', (1, 2))
    intervals.select('test', (3, 4))
    intervals.deselect_all()

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 0

    _check_lengths(mock, 1, 0, 3, 1)


def test_add_one_traj_3_intervals_select_2_deselect_one_by_one(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.select('test', (1, 2))
    intervals.select('test', (3, 4))
    intervals.deselect('test', (1, 2))
    intervals.deselect('test', (3, 4))

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 0

    _check_lengths(mock, 1, 0, 4, 1)


def test_add_one_traj_3_intervals_1_select_deselect_1_reselect(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.select('test', (1, 2))
    intervals.deselect('test', (1, 2))
    intervals.select('test', (1, 2))

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.selected_intervals('test')) == 1

    _check_lengths(mock, 1, 0, 3, 1)


def test_add_two_traj_3_intervals_multiple_select_deselect(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.update_intervals('test2', [(7, 8), (9, 10), (5, 6)])

    intervals.select('test', (1, 2))
    assert len(mock.s_changed) == 1

    intervals.deselect('test', (1, 2))
    assert len(mock.s_changed) == 2

    intervals.select('test', (1, 2))
    assert len(mock.s_changed) == 3

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.intervals('test2')) == 3
    assert len(intervals.selected_intervals('test')) == 1
    assert len(intervals.selected_intervals('test2')) == 0

    intervals.select('test2', (7, 8))
    assert len(intervals.selected_intervals('test')) == 1
    assert len(intervals.selected_intervals('test2')) == 1
    assert len(mock.s_changed) == 4

    intervals.deselect_all()  # emits two selection_changed signals
    assert mock.s_changed[-2] == 'test'
    assert mock.s_changed[-1] == 'test2'
    assert len(mock.s_changed) == 6
    intervals.select('test2', (7, 8))

    assert len(intervals.intervals('test')) == 3
    assert len(intervals.intervals('test2')) == 3
    assert len(intervals.selected_intervals('test')) == 0
    assert len(intervals.selected_intervals('test2')) == 1

    _check_lengths(mock, 2, 0, 7, 2)


def test_add_two_traj_3_same_intervals_select_deselect(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    intervals.update_intervals('test2', [(1, 2), (3, 4), (5, 6)])

    intervals.select('test', (1, 2))
    assert len(mock.s_changed) == 1
    assert len(intervals.selected_intervals('test')) == 1
    assert len(intervals.selected_intervals('test2')) == 0

    _check_lengths(mock, 2, 0, 1, 2)


def test_add_one_traj_3_intervals_select_change_intervals_still_selectioned(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])

    intervals.select('test', (1, 2))
    assert len(mock.s_changed) == 1
    assert len(intervals.selected_intervals('test')) == 1

    intervals.update_intervals('test', [(3, 4), (5, 6)])
    assert len(mock.s_changed) == 1
    assert len(intervals.selected_intervals('test')) == 1  # still selected

    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])
    assert len(mock.s_changed) == 1
    assert len(intervals.selected_intervals('test')) == 1  # still selected

    intervals.remove_trajectory('test')
    assert len(mock.s_changed) == 1
    with pytest.raises(KeyError):
        intervals.intervals('test')

    _check_lengths(mock, 3, 1, 1, 0)


def test_one_trajectory_get_names(mock):
    intervals.update_intervals('a', [])
    intervals.update_intervals('d', [])
    intervals.update_intervals('c', [])
    intervals.update_intervals('b', [])

    assert intervals.trajectory_names() == ['a', 'd', 'c', 'b']

    _check_lengths(mock, 4, 0, 0, 4)


def test_one_trajectory_get_interval_from_date(mock):
    intervals.update_intervals('test', [(1, 2), (3, 4), (5, 6)])

    assert intervals.interval_from_date('test', 2) == (1, 2)
    assert intervals.interval_from_date('test', 2.5) is None
    with pytest.raises(KeyError):
        intervals.interval_from_date('test2', 2)

    _check_lengths(mock, 1, 0, 0, 1)
