#!/usr/bin/env python3

import sys

from orbit_viewer.views.entities import EntitiesWidget
from orbit_viewer.entities import Entities

from PySide2 import QtWidgets


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    main = QtWidgets.QMainWindow()

    entities = Entities(main)
    w = EntitiesWidget(entities,main)
    main.setCentralWidget(w)
    main.show()

    sys.exit(app.exec_())
