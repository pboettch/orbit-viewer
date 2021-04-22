#!/usr/bin/env python3

import sys

from PySide2 import QtWidgets

from orbit_viewer import trajectories, OrbitViewer

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    main = QtWidgets.QMainWindow()

    w = OrbitViewer(main)
    w.set_trajectories(['mms1', 'cluster1'])

    main.setCentralWidget(w)

    main.show()

    app.aboutToQuit.connect(trajectories.clean_loaders)

    sys.exit(app.exec_())
