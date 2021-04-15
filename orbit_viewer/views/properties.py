from PySide2 import QtWidgets
from PySide2 import QtCore
from PySide2 import QtGui

from ..properties import PropertyHolder, Property


class PropertyBoolWidget(QtWidgets.QCheckBox):
    def __init__(self, prop: Property, parent=None):
        super().__init__(parent)

        self.prop = prop

        self.stateChanged.connect(prop.set)

    def update_visible_value(self):
        self.setChecked(self.prop.value)


class PropertyQColorWidget(QtWidgets.QWidget):
    def __init__(self, prop: Property, parent=None):
        super().__init__(parent)

        self.prop = prop

        button = QtWidgets.QPushButton("...", self)

        self.label = QtWidgets.QLabel(prop.name + ' color', alignment=QtCore.Qt.AlignCenter)
        self.label.setAutoFillBackground(True)

        l = QtWidgets.QHBoxLayout(self)
        l.addWidget(self.label)
        l.addWidget(button)

        options = QtWidgets.QColorDialog.DontUseNativeDialog | QtWidgets.QColorDialog.NoButtons
        if 'alpha' in prop.args and prop.args['alpha']:
            options |= QtWidgets.QColorDialog.ShowAlphaChannel

        self.color_dialog = QtWidgets.QColorDialog(self)
        self.color_dialog.setOptions(options)

        self.color_dialog.currentColorChanged.connect(prop.set)

        button.clicked.connect(self.color_dialog.show)

    def update_visible_value(self):
        self.color_dialog.setCurrentColor(self.prop.get())
        pal = self.label.palette()
        pal.setColor(QtGui.QPalette.Background, self.prop.get())
        self.label.setPalette(pal)


class PropertyLineEditWidget(QtWidgets.QLineEdit):
    def __init__(self, prop: Property, parent=None):
        super().__init__(parent)

        self.prop = prop

        if prop.type is float:
            valid = QtGui.QDoubleValidator(self)
            valid.setLocale(QtCore.QLocale.c())
        elif prop.type is int:
            valid = QtGui.QIntValidator(self)
            valid.setLocale(QtCore.QLocale.c())
        else:
            valid = None

        if valid:
            valid.setBottom(prop.args.get('minimum', float('-inf')))
            valid.setTop(prop.args.get('maximum', float('inf')))
            self.setValidator(valid)

        self.setReadOnly(prop.args.get('read_only', False))

        self.editingFinished.connect(self.editing_finished)

        self.inputRejected.connect(self.input_rejected)

    def editing_finished(self):
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Text, QtCore.Qt.green)
        self.setPalette(pal)
        self.prop.set(self.text())

    def input_rejected(self):
        pal = QtGui.QPalette()
        pal.setColor(QtGui.QPalette.Text, QtCore.Qt.red)
        self.setPalette(pal)

    def update_visible_value(self):
        self.setText(f'{self.prop.get()}')


class PropertySliderWidget(QtWidgets.QSlider):
    def __init__(self, prop: Property, parent=None):
        super().__init__(QtCore.Qt.Horizontal, parent)

        self.prop = prop

        self.setRange(prop.args['minimum'], prop.args['maximum'])
        self.valueChanged.connect(prop.set)

    def update_visible_value(self):
        self.setValue(self.prop.get())


class PropertyListWidget(QtWidgets.QComboBox):
    def __init__(self, prop: Property, parent=None):
        super().__init__(parent)

        self.prop = prop

        self.addItems([str(v) for v in prop.type])

        self.currentIndexChanged.connect(self.current_index_changed)

    def current_index_changed(self, index: int):
        if index in range(len(self.prop.type)):
            self.prop.set(self.prop.type[index])

    def update_visible_value(self):
        self.setCurrentIndex(self.prop.type.index(self.prop.get()))


class PropertyNotSupportedWidget(QtWidgets.QWidget):
    def __init__(self, prop: Property, parent=None):
        super().__init__(parent)

        label = QtWidgets.QLabel(str(prop.type) + ' not supported', self)

    def update_visible_value(self):
        pass


class PropertyEditorWidget(QtWidgets.QWidget):
    def __init__(self, prop_holder: PropertyHolder, parent=None):
        super().__init__(parent)

        self._property_widget = {}

        layout = QtWidgets.QGridLayout(self)
        layout.setAlignment(QtCore.Qt.AlignTop)

        for i, p in enumerate(prop_holder.properties()):

            widget = None
            if p.type == bool:
                widget = PropertyBoolWidget(p, self)

            elif p.type == QtGui.QColor:
                widget = PropertyQColorWidget(p, self)
            elif p.type in [float, str]:
                widget = PropertyLineEditWidget(p, self)
            elif p.type == int:
                # slider if min and max are set
                if 'minimum' in p.args and 'maximum' in p.args:
                    widget = PropertySliderWidget(p, self)
                else:
                    widget = PropertyLineEditWidget(p, self)
            elif type(p.type) == list:
                widget = PropertyListWidget(p, self)

            if not widget:
                widget = PropertyNotSupportedWidget(p, self)

            widget.sizePolicy().setHorizontalStretch(2)
            widget.setToolTip(p.desc)

            label = QtWidgets.QLabel(p.name, self)
            label.sizePolicy().setHorizontalStretch(1)

            layout.addWidget(label, i, 0)
            layout.addWidget(widget, i, 1)

            self._property_widget.setdefault(p, widget)

            widget.update_visible_value()

        prop_holder.property_has_changed.connect(self.property_has_changed)

    def property_has_changed(self, prop: Property):
        if prop in self._property_widget:
            print('new value for', prop.name, self._property_widget[prop])
            self._property_widget[prop].update_visible_value()
        else:
            print('not yet implemented')
