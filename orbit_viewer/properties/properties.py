from typing import Type

from PySide2 import QtCore


class Property:
    def __init__(self, holder, name: str, desc: str, ty: Type, value, **kwargs):
        self.holder = holder
        self.name = name
        self.desc = desc
        self.type = ty
        self.args = kwargs
        self.value = value

        self._block_recursion = False

    def set(self, v):
        if self._block_recursion:
            return

        self._block_recursion = True
        if isinstance(self.type, type):
            self.value = self.type(v)
        else:
            self.value = v
        self.holder.property_has_changed.emit(self)
        self._block_recursion = False

    def get(self):
        return self.value


class PropertyHolder(QtCore.QObject):
    property_has_changed = QtCore.Signal(Property)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._properties = []

    def properties(self):
        return self._properties

    def add_property(self, *args, **kwargs):
        prop = Property(self, *args, **kwargs)
        self._properties.append(prop)
        return prop

    def set(self, name: str, value):
        for p in self._properties:
            if p.name == name:
                p.set(value)
                break
        else:
            raise KeyError('no property with name ' + name)
