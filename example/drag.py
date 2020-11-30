#!/usr/bin/env python3

import sys

from PySide2.QtWidgets import (
    QApplication,
)

from PySide2.QtGui import (
    QVector3D,
    QColor,
)

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender


class MyObj(Qt3DCore.QEntity):
    def __init__(self, mesh: Qt3DCore.QEntity, *args, **kwargs):
        super().__init__(*args, **kwargs)

        mesh.setParent(self)
        self.addComponent(mesh)

        self.material = Qt3DExtras.QPhongMaterial(self)
        self.material.setDiffuse(QColor(200, 0, 0))
        self.addComponent(self.material)

        picker = Qt3DRender.QObjectPicker(self)
        picker.setHoverEnabled(True)
        picker.setDragEnabled(True)
        self.addComponent(picker)

        self.trans = Qt3DCore.QTransform(self)
        self.addComponent(self.trans)


        picker.entered.connect(self.entered)
        picker.exited.connect(self.exited)
        picker.moved.connect(self.moved)

        picker.pressed.connect(self.pressed)
        picker.released.connect(self.released)

        self._camera = None
        self._cam_ctrl = None

    def entered(self):
        print('hello')
        self.material.setDiffuse(QColor(0, 200, 0))

    def exited(self):
        print('olleh')
        self.material.setDiffuse(QColor(200, 0, 0))

    def moved(self, event: Qt3DRender.QPickEvent):
        if event.buttons() & Qt3DRender.QPickEvent.LeftButton:

            self.trans.setTranslation(QVector3D(
                event.worldIntersection().x(),
                event.worldIntersection().y(),
                self.trans.translation().z()))

            for c in event.entity().components():
                print(c)

        print('moved', event.buttons(), event.worldIntersection() )

    def pressed(self):
        print('pressed')
        self._cam_ctrl.setEnabled(False)

    def released(self):
        print('released')
        self._cam_ctrl.setEnabled(True)

    def setCamera(self, camera: Qt3DRender.QCamera):
        self._camera = camera

    def setCameraController(self, ctrl: Qt3DExtras.QAbstractCameraController):
        self._cam_ctrl = ctrl


if __name__ == "__main__":
    app = QApplication(sys.argv)

    view = Qt3DExtras.Qt3DWindow()
    view.setTitle("3D PySide2")
    view.defaultFrameGraph().setClearColor(QColor(210, 210, 220))


    # scene = Scene()
    root = Qt3DCore.QEntity()

    mesh = Qt3DExtras.QSphereMesh()
    mesh.setRadius(4)

    s1 = MyObj(mesh, root)

    # Camera
    camera = view.camera()
    camera.lens().setPerspectiveProjection(65.0, 16.0 / 9.0, 0.1, 200.0)
    camera.setPosition(QVector3D(0, 0, 50.0))
    camera.setViewCenter(QVector3D(0, 0, 0))
    camera.viewMatrix()

    s1.setCamera(camera)

    camController = Qt3DExtras.QOrbitCameraController(root)
    camController.setCamera(camera)

    s1.setCameraController(camController)

    # light_entity = Qt3DCore.QEntity(camera)
    light_entity = Qt3DCore.QEntity(root)
    light = Qt3DRender.QPointLight(light_entity)
    light.setColor("white")
    light.setIntensity(1)
    light_entity.addComponent(light)

    trans = Qt3DCore.QTransform(light_entity)
    trans.setTranslation(QVector3D(0, 0, 50))
    light_entity.addComponent(trans)

    view.setRootEntity(root)
    view.show()

    sys.exit(app.exec_())
