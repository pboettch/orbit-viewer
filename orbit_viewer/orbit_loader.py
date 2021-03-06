import datetime as dt

import PySide2.QtCore as QtCore

import spwc


class OrbitLoader(QtCore.QThread):
    """
    QThread based OrbitLoader class (using SPWC) one request at a time.

    Queue-compression for requested ranges: only last requested range is loaded if multiple get_orbit()-calls received
    while loading was on-going.
    """

    __load = QtCore.Signal()
    error = QtCore.Signal(str)
    done = QtCore.Signal(spwc.SpwcVariable)

    def __init__(self, product, parent=None):
        super().__init__(parent)

        self._product = product

        self._mutex = QtCore.QMutex()

        self._ssc = spwc.SscWeb()
        self._range = None
        self._last_range = None

        self.moveToThread(self)

        self.__load.connect(self.__get_orbit)

        self.start()

    def get_orbit(self, start: dt.datetime, stop: dt.datetime):
        self._mutex.lock()
        self._range = (start, stop)
        self._mutex.unlock()
        self.__load.emit()

    @QtCore.Slot()
    def __get_orbit(self):
        try:
            self._mutex.lock()
            r = self._range
            self._mutex.unlock()

            if r == self._last_range:  # range already loaded - compression
                return

            var = self._ssc.get_orbit(product=self._product,
                                      start_time=r[0],
                                      stop_time=r[1],
                                      coordinate_system='gse')

            if var is None:
                self.error.emit(f'OrbitLoader: no data could be retrieved for "{self._product}" in given range')
                return

            self._last_range = r
            self.done.emit(var)

        except Exception as e:
            self.error.emit('OrbitLoader: SPWC exception "' + str(e) + '"')
