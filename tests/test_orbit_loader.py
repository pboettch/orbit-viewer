#!/usr/bin/env python3

import datetime as dt

from orbit_viewer.orbit_loader import OrbitLoader

import spwc


def test_get_orbit_mms1_1_hours_sanity_check(qtbot):
    s = OrbitLoader('mms1')

    var = None
    error_count = 0

    def __done(product: str, v: spwc.SpwcVariable):
        assert product == 'mms1'
        nonlocal var
        assert var is None
        var = v

    def __error(product):
        assert product == 'mms1'
        nonlocal var
        nonlocal error_count
        error_count += 1

    s.done.connect(__done)
    s.error.connect(__error)

    with qtbot.waitSignal(s.done, timeout=10000):
        r = (dt.datetime.now() - dt.timedelta(hours=1), dt.datetime.now())
        s.get_orbit(r[0], r[1])

    with qtbot.waitSignal(s.finished):
        s.quit()

    assert var is not None
    assert len(var.time) == 60
    assert var.data.shape == (60, 3)
    assert error_count == 0


def test_error_unknown_product(qtbot):
    s = OrbitLoader('surely_not_existing')
    error_product = ''
    error_count = 0
    done_count = 0

    def __done(product: str, v: spwc.SpwcVariable):
        assert product == 'surely_not_existing'
        nonlocal done_count
        done_count += 1

    def __error(product: str):
        nonlocal error_product,error_count
        error_product = product
        error_count += 1

    s.error.connect(__error)

    with qtbot.waitSignal(s.error, timeout=5000):
        r = (dt.datetime.now() - dt.timedelta(hours=1), dt.datetime.now())
        s.get_orbit(r[0], r[1])

    with qtbot.waitSignal(s.finished):
        s.quit()

    assert error_product == 'surely_not_existing'
    assert error_count == 1
    assert done_count == 0


def test_invalid_time_range_empty_orbit(qtbot):
    s = OrbitLoader('mms1')

    var = None
    error_count = 0

    def __done(product: str, v: spwc.SpwcVariable):
        assert product == 'mms1'
        nonlocal var
        var = v

    def __error(product: str):
        assert product == 'mms1'
        nonlocal error_count
        error_count += 1

    s.done.connect(__done)
    s.error.connect(__error)

    with qtbot.waitSignal(s.error, timeout=1000):
        r = (dt.datetime.now() + dt.timedelta(hours=1), dt.datetime.now())
        s.get_orbit(r[0], r[1])

    with qtbot.waitSignal(s.finished):
        s.quit()

    assert var is None
    assert error_count == 1
