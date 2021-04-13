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

        self._lower_layer = Qt3DRender.QLayer()
        layer_filter = Qt3DRender.QLayerFilter(camera_selector)
        layer_filter.addLayer(self._lower_layer)

        self._middle_layer = Qt3DRender.QLayer()
        layer_filter = Qt3DRender.QLayerFilter(camera_selector)
        layer_filter.addLayer(self._middle_layer)

        self._higher_layer = Qt3DRender.QLayer()
        layer_filter = Qt3DRender.QLayerFilter(camera_selector)
        layer_filter.addLayer(self._higher_layer)

        self.setActiveFrameGraph(render_surface_selector)

        # Camera
        camera = self.camera()
        camera.lens().setPerspectiveProjection(65.0, 16.0 / 9.0, 0.1, 1000.0)
        camera.setPosition(QtGui.QVector3D(0, 100, 0))
        #camera.setViewCenter(QtGui.QVector3D(1, 0, 0))

        cam_ctrl = Qt3DExtras.QOrbitCameraController(self._scene)
        cam_ctrl.setCamera(camera)
        cam_ctrl.setLinearSpeed(500.)

        # Light follows camera source
        self.light_entity = Qt3DCore.QEntity(camera)
        light = Qt3DRender.QPointLight(camera)
        light.setColor("white")
        light.setIntensity(1)
        self.light_entity.addComponent(light)
        # has to be added all layers
        self.light_entity.addComponent(self._middle_layer)
        self.light_entity.addComponent(self._lower_layer)
        self.light_entity.addComponent(self._higher_layer)

    def middle_layer(self):
        return self._middle_layer

    def lower_layer(self):
        return self._lower_layer

    def higher_layer(self):
        return self._higher_layer

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        camera_aspect = e.size().width() / e.size().height()
        self.camera().lens().setPerspectiveProjection(65.0, camera_aspect, 0.1, 1000.0)

    def scene(self):
        return self._scene
