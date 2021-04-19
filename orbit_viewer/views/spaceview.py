from PySide2 import QtGui

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender


class SpaceView(Qt3DExtras.Qt3DWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._scene = Qt3DCore.QEntity()
        self.setRootEntity(self._scene)

        sort_policy = Qt3DRender.QSortPolicy(self._scene)
        sort_policy.setSortTypes([Qt3DRender.QSortPolicy.BackToFront])

        render_surface_selector = Qt3DRender.QRenderSurfaceSelector(sort_policy)
        render_surface_selector.setSurface(self)

        clear_buffers = Qt3DRender.QClearBuffers(render_surface_selector)
        clear_buffers.setBuffers(Qt3DRender.QClearBuffers.AllBuffers)
        clear_buffers.setClearColor(QtGui.QColor.fromRgb(30, 30, 30))
        self.__no_draw = Qt3DRender.QNoDraw(clear_buffers)

        viewport = Qt3DRender.QViewport(render_surface_selector)

        camera_selector = Qt3DRender.QCameraSelector(viewport)
        camera_selector.setCamera(self.camera())

        self._alpha_layers = []
        for _ in range(256):
            layer = Qt3DRender.QLayer()
            layer_filter = Qt3DRender.QLayerFilter(camera_selector)
            layer_filter.addLayer(layer)
            self._alpha_layers += [layer]
        self._alpha_layers = self._alpha_layers[::-1]

        self.setActiveFrameGraph(render_surface_selector)

        # Camera
        camera = self.camera()

        camera.setPosition(QtGui.QVector3D(0, 0, 100))
        camera.setViewCenter(QtGui.QVector3D(0, 0, .1))
        # camera.setUpVector(QtGui.QVector3D(0.0, 1.0, 0.0))

        camera.lens().setPerspectiveProjection(35, 1, 1, 10000.0)
        cam_ctrl = Qt3DExtras.QOrbitCameraController(self._scene)
        cam_ctrl.setCamera(camera)

        cam_ctrl.setLookSpeed(-135)
        cam_ctrl.setAcceleration(0)
        cam_ctrl.setLinearSpeed(-135)

        # Light follows camera source
        self.light_entity = Qt3DCore.QEntity(camera)
        light = Qt3DRender.QPointLight(camera)
        light.setColor("white")
        light.setIntensity(1)
        self.light_entity.addComponent(light)

        # has to be added all layers
        for layer in self._alpha_layers:
            self.light_entity.addComponent(layer)

    def alpha_layers(self, i: int) -> Qt3DRender.QLayer:
        return self._alpha_layers[i]

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        camera_aspect = e.size().width() / e.size().height()
        self.camera().lens().setAspectRatio(camera_aspect)

    def scene(self):
        return self._scene
