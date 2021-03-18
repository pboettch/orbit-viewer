#!/usr/bin/env python3
import sys

from PySide2 import QtWidgets, QtCore, QtGui
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DRender import Qt3DRender
from PySide2.Qt3DInput import Qt3DInput


class My3DWindow(Qt3DExtras.Qt3DWindow):
    signalPresskey = QtCore.Signal(QtGui.QKeyEvent)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.Scene = Qt3DCore.QEntity()
        self.setRootEntity(self.Scene)

        renderSurfaceSelector = Qt3DRender.QRenderSurfaceSelector(self.Scene)
        renderSurfaceSelector.setSurface(self)

        clearBuffers = Qt3DRender.QClearBuffers(renderSurfaceSelector)
        clearBuffers.setBuffers(Qt3DRender.QClearBuffers.AllBuffers)
        clearBuffers.setClearColor(QtCore.Qt.gray)

        noDraw = Qt3DRender.QNoDraw(clearBuffers)

        viewport = Qt3DRender.QViewport(renderSurfaceSelector)
        cameraSelector = Qt3DRender.QCameraSelector(viewport)
        cameraSelector.setCamera(self.camera())

        self.OpaqueLayer = Qt3DRender.QLayer(self.Scene)
        opaqueFilter = Qt3DRender.QLayerFilter(cameraSelector)
        opaqueFilter.addLayer(self.OpaqueLayer)

        self.TransparentLayer = Qt3DRender.QLayer(self.Scene)
        transparentFilter = Qt3DRender.QLayerFilter(cameraSelector)
        transparentFilter.addLayer(self.TransparentLayer)

        self.setActiveFrameGraph(renderSurfaceSelector)

        self.camera().lens().setPerspectiveProjection(45.0, 16.0 / 9.0, 0.1, 1000.0)
        self.camera().setPosition(QtGui.QVector3D(0.0, 0.0, 100.0))
        self.camera().setViewCenter(QtGui.QVector3D(0.0, 0.0, 0.0))

        #cameraController = Qt3DExtras.QFirstPersonCameraController(self.Scene)
        #cameraController.setCamera(self.camera())
        cam_ctrl = Qt3DExtras.QOrbitCameraController(self.Scene)
        cam_ctrl.setCamera(self.camera())

        self.light_entity = Qt3DCore.QEntity(self.camera())  # light follows camera source
        light = Qt3DRender.QPointLight(self.light_entity)
        light.setColor("white")
        light.setIntensity(1)
        self.light_entity.addComponent(light)
        self.light_entity.addComponent(self.OpaqueLayer)
        self.light_entity.addComponent(self.TransparentLayer)

    def resizeEvent(self, e: QtGui.QResizeEvent):
        camera_aspect = e.size().width() / e.size().height()
        self.camera().lens().setPerspectiveProjection(45.0, camera_aspect, 0.1, 1000.0)

    def keyPressEvent(self, k: QtGui.QKeyEvent) -> None:
        self.signalPresskey.emit(k)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = My3DWindow()
    sphere1 = Qt3DCore.QEntity(window.Scene)
    sphere2 = Qt3DCore.QEntity(window.Scene)

    transform1 = Qt3DCore.QTransform(sphere1)
    transform1.setTranslation(QtGui.QVector3D(5.0, 0.0, -10.0))

    transform2 = Qt3DCore.QTransform(sphere2)
    transform2.setTranslation(QtGui.QVector3D(-5.0, 0.0, -10.0))

    material1 = Qt3DExtras.QPhongAlphaMaterial(sphere1)
    material1.setAmbient(QtCore.Qt.blue)

    material2 = Qt3DExtras.QPhongMaterial(sphere2)
    material2.setAmbient(QtCore.Qt.red)

    spheremesh1 = Qt3DExtras.QSphereMesh(sphere1)
    spheremesh1.setRadius(15.0)
    spheremesh1.setSlices(32)
    spheremesh1.setRings(32)

    spheremesh2 = Qt3DExtras.QSphereMesh(sphere2)
    spheremesh2.setRadius(15.0)
    spheremesh2.setSlices(32)
    spheremesh2.setRings(32)

    sphere1.addComponent(material1)
    sphere1.addComponent(spheremesh1)
    sphere1.addComponent(transform1)
    sphere1.addComponent(window.TransparentLayer)

    sphere2.addComponent(material2)
    sphere2.addComponent(spheremesh2)
    sphere2.addComponent(transform2)
    sphere2.addComponent(window.OpaqueLayer)


    def func(e: QtGui.QKeyEvent):
        if e.key() == QtCore.Qt.Key_S:
            transform2.setTranslation(transform2.translation() + QtGui.QVector3D(0.0, 0.0, 1.0))
        elif e.key() == QtCore.Qt.Key_W:
            transform2.setTranslation(transform2.translation() + QtGui.QVector3D(0.0, 0.0, -1.0))
        elif e.key() == QtCore.Qt.Key_A:
            transform2.setTranslation(transform2.translation() + QtGui.QVector3D(-1, 0.0, 0.0))
        elif e.key() == QtCore.Qt.Key_D:
            transform2.setTranslation(transform2.translation() + QtGui.QVector3D(1, 0.0, 0.0))


    window.signalPresskey.connect(func)

    window.show()
    sys.exit(app.exec_())
