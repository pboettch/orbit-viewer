from matplotlib.backend_bases import MouseEvent, MouseButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import matplotlib.colors as mcolors
import matplotlib.dates as mdates

from orbit_viewer import trajectories

import datetime as dt

from PySide2 import QtCore

from typing import List

from dataclasses import dataclass, field

@dataclass
class _Timeline:
    name: str
    y_offset: float
    y_height: float
    color: str
    interval_bars: List = field(default_factory=list)
    selection_bars: List = field(default_factory=list)

    @property
    def y_range(self):
        return self.y_offset, self.y_offset + self.y_height

    @property
    def y(self):
        return self.y_offset, self.y_height


class Timelines(FigureCanvasQTAgg):
    range_changed = QtCore.Signal(dt.datetime, dt.datetime)

    def __init__(self, initial_start: dt.datetime, initial_stop: dt.datetime):
        fig = Figure()
        super().__init__(fig)

        # to allow key-modifiers be present in MouseEvent
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        # state-variable for interacting with plot (panning, zooming, selecting, highlight)
        self._panning_start_data = None
        self._panning_start_pixel = None
        self._select_multiple = None
        self._select_data = None
        self._highlight_bar = None

        # graphical representation of timelines
        self._timelines = {}

        # global trajectory model
        trajectories.intervals_changed.connect(self._intervals_changed)
        trajectories.selection_changed.connect(self._selection_changed)
        trajectories.trajectory_removed.connect(self._trajectory_removed)

        # delayed signal submission
        self._range_changed_timer = QtCore.QTimer(self)
        self._range_changed_timer.setSingleShot(True)
        self._range_changed_timer.timeout.connect(self._range_changed)

        self._axes = fig.add_subplot(111)
        self._axes.set_xlim(initial_start, initial_stop)
        self._axes.set_yticks([])

        self.mpl_connect('motion_notify_event', self._move)
        self.mpl_connect('scroll_event', self._scroll)
        self.mpl_connect('button_press_event', self._pressed)
        self.mpl_connect('button_release_event', self._released)

    def _pan(self, xpixel: int, xdata):
        if self._panning_start_data is None:
            return False

        # do not start to pan before at least 3 pixels have been moved - avoid spurious movements when selecting
        if self._panning_start_pixel is not None and abs(self._panning_start_pixel - xpixel) < 3:
            return False

        # started to pan
        self._panning_start_pixel = None

        delta = self._panning_start_data - xdata

        old_range = self._axes.get_xlim()
        self._axes.set_xlim(old_range[0] + delta,
                            old_range[1] + delta)

        self._range_changed_timer.start(200)

        self._panning_start_data = xdata + delta

        return True

    def _highlight(self, ydata: float, xdata):
        tl = self._timeline_from_y(ydata)
        if tl is not None:
            for interval in trajectories.intervals(tl.name):
                if interval[0] <= mdates.num2epoch(xdata) <= interval[1]:
                    if self._highlight_bar is not None:
                        self._highlight_bar.remove()
                    self._highlight_bar = self._axes.broken_barh([(mdates.epoch2num(interval[0]),
                                                                   mdates.epoch2num(interval[1] - interval[0]))],
                                                                 tl.y,
                                                                 facecolor="None",
                                                                 edgecolor='red',
                                                                 linewidth=2)
                    return True

        if self._highlight_bar is not None:
            self._highlight_bar.remove()
            self._highlight_bar = None

            return True

        return False

    def _move(self, event: MouseEvent):
        if event.inaxes != self._axes:
            return

        if event.button == MouseButton.LEFT:
            redraw = self._pan(event.x, event.xdata)
        else:
            redraw = self._highlight(event.ydata, event.xdata)

        if redraw:
            self.figure.canvas.draw()

    def _pressed(self, event: MouseEvent):
        if event.inaxes != self._axes:
            return

        if event.button == MouseButton.LEFT:
            self._panning_start_data = event.xdata
            self._panning_start_pixel = event.x  # used for panning-start threshold - set to None if panning started

            self._select_data = (event.xdata, event.ydata)
            self._select_multiple = event.key is not None and 'control' in event.key

    def _released(self, event: MouseEvent):
        if event.button == MouseButton.LEFT:
            self._panning_start_data = None

            if self._panning_start_pixel is not None:  # panning has not stated - selection

                if not self._select_multiple:
                    trajectories.deselect_all_intervals()

                tl = self._timeline_from_y(self._select_data[1])
                if tl is not None:
                    interval = trajectories.interval_from_date(tl.name, mdates.num2epoch(self._select_data[0]))
                    if interval:
                        if interval in trajectories.selected_intervals(tl.name):
                            trajectories.deselect_interval(tl.name, interval)
                        else:
                            trajectories.select_interval(tl.name, interval)

    def _scroll(self, event: MouseEvent):
        if event.inaxes != self._axes:
            return

        if event.button == 'down':
            factor = 1.1
        elif event.button == 'up':
            factor = 0.9

        old_range = self._axes.get_xlim()
        center_val = event.xdata
        offset = center_val * (1 - factor)

        self._axes.set_xlim(factor * old_range[0] + offset,
                            factor * old_range[1] + offset)

        self.figure.canvas.draw()
        self._range_changed_timer.start(200)

    def _clear_timeline(self, timeline: _Timeline):
        for bar in timeline.interval_bars:
            bar.remove()
        timeline.interval_bars = []

    def _clear_timeline_selection(self, timeline: _Timeline):
        for bar in timeline.selection_bars:
            bar.remove()
        timeline.selection_bars = []

    def _redraw_timeline(self, name: str):
        timeline = self._timelines[name]

        self._clear_timeline(timeline)

        line_height = 0.5

        whole_range = self._axes.get_xlim()
        barh = self._axes.broken_barh([(whole_range[0], whole_range[1] - whole_range[0])],
                                      (timeline.y_offset + timeline.y_height / 2 - line_height / 2, line_height),
                                      facecolors=timeline.color)
        timeline.interval_bars.append(barh)

        # interval bars
        for interval in trajectories.intervals(name):
            barh = self._axes.broken_barh([(mdates.epoch2num(interval[0]),
                                            mdates.epoch2num(interval[1] - interval[0]))],
                                          timeline.y,
                                          facecolors=timeline.color)

            timeline.interval_bars.append(barh)

    def _redraw_selection(self, name: str):
        timeline = self._timelines[name]

        self._clear_timeline_selection(timeline)

        for interval in trajectories.selected_intervals(timeline.name):
            barh = self._axes.broken_barh([(mdates.epoch2num(interval[0]),
                                            mdates.epoch2num(interval[1] - interval[0]))],
                                          timeline.y,
                                          facecolor="None",
                                          edgecolors='black',
                                          linewidth=2)
            timeline.selection_bars.append(barh)

    def _redraw(self):
        y_height = 14
        y_start = 2
        y_offset = y_start
        y_delta = 15

        labels = []

        for tl in self._timelines.values():
            print('clearing', tl)
            self._clear_timeline(tl)
            self._clear_timeline_selection(tl)

        self._timelines = {}

        for i, name in enumerate(sorted(trajectories.names())):
            print('adding', name)
            color = list(mcolors.TABLEAU_COLORS.values())[i % len(mcolors.TABLEAU_COLORS)]

            self._timelines[name] = _Timeline(name, y_offset, y_height, color)

            self._redraw_timeline(name)
            self._redraw_selection(name)

            labels.append(name)

            y_offset += y_delta

        self._axes.set_yticks([*range(y_start + y_height // 2, y_offset, y_delta)])
        self._axes.set_yticklabels(labels)
        if y_start != y_offset:
            self._axes.set_ylim(y_start, y_offset - 1)

        self.figure.canvas.draw()

    def _timeline_from_y(self, y):
        for tl in self._timelines.values():
            if tl.y_range[0] <= y <= tl.y_range[1]:
                return tl
        return None

    def _intervals_changed(self, name: str):
        if name in self._timelines:  # update
            self._redraw_timeline(name)
            self._redraw_selection(name)
            self.figure.canvas.draw()
        else:  # newly added
            self._redraw()

    def _selection_changed(self, name: str):
        self._redraw_selection(name)
        self.figure.canvas.draw()

    def _trajectory_removed(self, name: str):
        self._redraw()

    def range(self):
        range = self._axes.get_xlim()
        return mdates.num2date(range[0]), mdates.num2date(range[1])

    def _range_changed(self):
        self.range_changed.emit(*self.range())
