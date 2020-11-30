#!/usr/bin/env python3

import sys

import numpy as np

# from spwc import sscweb

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender

from PySide2.QtWidgets import (
    QApplication,
)

from PySide2.QtGui import (
    QVector3D,
    QQuaternion,
    QMatrix4x4,
    QColor,
)

from PySide2.QtCore import (
    QObject,
    Property,
    Signal,

    QPropertyAnimation,
    QByteArray,

    qFuzzyCompare,
    QSize
)

class PointGeometry(Qt3DRender.QGeometry):
    def __init__(self, position: QVector3D, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.vertexBuffer = Qt3DRender.QBuffer()
        self.indexBuffer = Qt3DRender.QBuffer()
        self.positionAttribute = Qt3DRender.QAttribute()
        self.indexAttribute = Qt3DRender.QAttribute()

        self.positionAttribute.setName(Qt3DRender.QAttribute.defaultPositionAttributeName())
        self.positionAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        self.positionAttribute.setVertexSize(3)
        self.positionAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.positionAttribute.setBuffer(self.vertexBuffer)
        self.positionAttribute.setByteStride(0)
        self.positionAttribute.setCount(3)

        self.indexAttribute.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        self.indexAttribute.setVertexBaseType(Qt3DRender.QAttribute.UnsignedShort)
        self.indexAttribute.setBuffer(self.indexBuffer)
        self.indexAttribute.setCount(1)

        self.data = PointGeometry.createPointVertexData(position)
        self.vertexBuffer.setData(self.data)

        self.index = PointGeometry.createPointIndexData()
        self.vertexBuffer.setData(self.index)

        self.addAttribute(self.positionAttribute)
        self.addAttribute(self.indexAttribute)

    def createPointVertexData(position: QVector3D):
        data = np.array((position.x(), position.y(), position.z()), dtype=np.single)
        assert len(data.tobytes()) == 12
        print([hex(c) for c in data.tobytes()])
        return data.tobytes()

    def createPointIndexData():
        data = np.array([0], dtype=np.uint16)
        assert len(data.tobytes()) == 2
        print(data)
        return data.tobytes()


class Point(Qt3DRender.QGeometryRenderer):
    def __init__(self, position: QVector3D, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._geometry = PointGeometry(position)
        self.setPrimitiveType(Qt3DRender.QGeometryRenderer.Points)

        self.setGeometry(self._geometry)


class Plane(Qt3DCore.QEntity):



    def __init__(self, w: float, h: float, resolution: QSize, color: QColor, mirrored: bool = False,
                 *args, **kwargs):

        super().__init__(*args, **kwargs)

        self._geo = Qt3DRender.QGeometry(self)

        self.positionAttribute = Qt3DRender.QAttribute(self._geo)
        self.normalAttribute = Qt3DRender.QAttribute(self._geo)
        self.texCoordAttribute = Qt3DRender.QAttribute(self._geo)
        self.tangentAttribute = Qt3DRender.QAttribute(self._geo)
        self.indexAttribute = Qt3DRender.QAttribute(self._geo)
        self.vertexBuffer = Qt3DRender.QBuffer(self._geo)
        self.indexBuffer = Qt3DRender.QBuffer(self._geo)

        nVerts = resolution.width() * resolution.height()
        stride = (3 + 2 + 3 + 4) * 4  # sizeof(float);
        faces = 2 * (resolution.width() - 1) * (resolution.height() - 1)

        self.positionAttribute.setName(Qt3DRender.QAttribute.defaultPositionAttributeName())
        self.positionAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        self.positionAttribute.setVertexSize(3)
        self.positionAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.positionAttribute.setBuffer(self.vertexBuffer)
        self.positionAttribute.setByteStride(stride)
        self.positionAttribute.setCount(nVerts)

        self.texCoordAttribute.setName(Qt3DRender.QAttribute.defaultTextureCoordinateAttributeName())
        self.positionAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        self.texCoordAttribute.setVertexSize(2)
        self.texCoordAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.texCoordAttribute.setBuffer(self.vertexBuffer)
        self.texCoordAttribute.setByteStride(stride)
        self.texCoordAttribute.setByteOffset(3 * 4)
        self.texCoordAttribute.setCount(nVerts)

        self.normalAttribute.setName(Qt3DRender.QAttribute.defaultNormalAttributeName())
        self.normalAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        self.normalAttribute.setVertexSize(3)
        self.normalAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.normalAttribute.setBuffer(self.vertexBuffer)
        self.normalAttribute.setByteStride(stride)
        self.normalAttribute.setByteOffset(5 * 4)
        self.normalAttribute.setCount(nVerts)

        self.tangentAttribute.setName(Qt3DRender.QAttribute.defaultTangentAttributeName())
        self.tangentAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        self.tangentAttribute.setVertexSize(4)
        self.tangentAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.tangentAttribute.setBuffer(self.vertexBuffer)
        self.tangentAttribute.setByteStride(stride)
        self.tangentAttribute.setByteOffset(8 * 4)
        self.tangentAttribute.setCount(nVerts)

        self.indexAttribute.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        self.indexAttribute.setVertexBaseType(Qt3DRender.QAttribute.UnsignedShort)
        self.indexAttribute.setBuffer(self.indexBuffer)

        # Each primitive has 3 vertives
        self.indexAttribute.setCount(faces * 3)

        self.vertexBuffer.setData(Plane.createPlaneVertexData(w, h, resolution, mirrored))
        self.indexBuffer.setData(Plane.createPlaneIndexData(resolution))

        self._geo.addAttribute(self.positionAttribute)
        self._geo.addAttribute(self.texCoordAttribute)
        self._geo.addAttribute(self.normalAttribute)
        self._geo.addAttribute(self.tangentAttribute)
        self._geo.addAttribute(self.indexAttribute)

        # mesh
        self.mesh = Qt3DRender.QGeometryRenderer(self)
        self.mesh.setGeometry(self._geo)
        self.mesh.setPrimitiveType(Qt3DRender.QGeometryRenderer.TriangleFan)

        self.material = Qt3DExtras.QPhongMaterial(self)
        self.material.setAmbient(color)

        self.addComponent(self.mesh)
        self.addComponent(self.material)


class Line(Qt3DCore.QEntity):
    def __init__(self,
                 points: np.array,
                 color: QColor,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        print(points, points.shape, points.dtype, len(points.tobytes()))

        self._geo = Qt3DRender.QGeometry(self)

        # position vertices (start and end)
        self.buffer = Qt3DRender.QBuffer(self._geo)
        self.buffer.setData(points.tobytes())

        print(self.buffer.data().size())

        self.positionAttribute = Qt3DRender.QAttribute(self._geo)
        self.positionAttribute.setName(Qt3DRender.QAttribute.defaultPositionAttributeName())
        self.positionAttribute.setVertexBaseType(Qt3DRender.QAttribute.Double)
        self.positionAttribute.setVertexSize(3)
        self.positionAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        self.positionAttribute.setBuffer(self.buffer)
        self.positionAttribute.setByteStride(points.shape[1] * 8)  # sizeof(float)
        self.positionAttribute.setCount(points.shape[0])
        self._geo.addAttribute(self.positionAttribute)  # We add the vertices in the geometry

        # connectivity between vertices
        self.indices = np.arange(0, points.shape[0], dtype=np.uint32).tobytes()

        self.indexBuffer = Qt3DRender.QBuffer(self._geo)
        self.indexBuffer.setData(self.indices)

        self.indexAttribute = Qt3DRender.QAttribute(self._geo)
        self.indexAttribute.setVertexBaseType(Qt3DRender.QAttribute.UnsignedInt)
        self.indexAttribute.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        self.indexAttribute.setBuffer(self.indexBuffer)
        self.indexAttribute.setCount(points.shape[0])
        self._geo.addAttribute(self.indexAttribute)  # We add the indices linking the points in the geometry

        # mesh
        self.line = Qt3DRender.QGeometryRenderer(self)
        self.line.setGeometry(self._geo)
        self.line.setPrimitiveType(Qt3DRender.QGeometryRenderer.TriangleStrip)

        self.material = Qt3DExtras.QPhongMaterial(self)
        self.material.setAmbient(color)

        self.addComponent(self.line)
        self.addComponent(self.material)


class OrbitTransformController(QObject):
    def __init__(self, turn_vector: QVector3D, pos: QVector3D, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._radius = 1.0
        self._angle = 0
        self._target = None
        self._matrix = QMatrix4x4()
        self._turn = turn_vector
        self._pos = pos

    def setTarget(self, target: Qt3DCore.QTransform):
        if self._target != target:
            self._target = target
            self.targetChanged.emit()

    def target(self):
        return self._target

    def setRadius(self, radius: float):
        if not qFuzzyCompare(radius, self._radius):
            self._radius = radius
            self._updateMatrix()
            self.radiusChanged.emit()

    def radius(self):
        return self._radius

    def setAngle(self, angle: float):
        if not qFuzzyCompare(angle, self._angle):
            self._angle = angle
            self._updateMatrix()
            self.angleChanged.emit()

    def angle(self):
        return self._angle

    def _updateMatrix(self):
        self._matrix.setToIdentity()
        self._matrix.rotate(self._angle, self._turn)
        self._matrix.translate(self._radius + self._pos.x(), self._pos.y(), self._pos.z())
        self._target.setMatrix(self._matrix)

    target = Property(Qt3DCore.QTransform, target, setTarget)
    radius = Property(float, radius, setRadius)
    angle = Property(float, angle, setAngle)

    targetChanged = Signal()
    radiusChanged = Signal()
    angleChanged = Signal()




class Sphere(Qt3DCore.QEntity):
    def __init__(self, root, pos, rad, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.sphereEntity = Qt3DCore.QEntity(root)
        self.sphereMesh = Qt3DExtras.QSphereMesh()
        self.sphereMesh.setRadius(rad)
        self.sphereMesh.setGenerateTangents(True)

        self.sphereTransform = Qt3DCore.QTransform()
        self.sphereTransform.setTranslation(pos)

        self.sphereEntity.addComponent(self.sphereMesh)
        self.sphereEntity.addComponent(self.sphereTransform)

        self.material = Qt3DExtras.QPhongMaterial(root)
        self.sphereEntity.addComponent(self.material)


class Scene(Qt3DCore.QEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.material = Qt3DExtras.QPhongMaterial(self)

        # self.torusEntity = Qt3DCore.QEntity(self)
        # self.torusMesh = Qt3DExtras.QTorusMesh()
        # self.torusMesh.setRadius(5)
        # self.torusMesh.setMinorRadius(1)
        # self.torusMesh.setRings(100)
        # self.torusMesh.setSlices(20)

        # self.torusTransform = Qt3DCore.QTransform()
        # self.torusTransform.setScale3D(QVector3D(1.5, 1, 0.5))
        # self.torusTransform.setTranslation(QVector3D(0, 0, 0))  # position
        # self.torusTransform.setRotation(QQuaternion.fromAxisAndAngle(QVector3D(1, 0, 0), 45.0))

        # self.torusEntity.addComponent(self.torusMesh)
        # self.torusEntity.addComponent(self.torusTransform)
        # self.torusEntity.addComponent(self.material)

        # self.cuboid = Qt3DExtras.QCuboidMesh()
        # # CuboidMesh Transform
        # self.cuboidTransform = Qt3DCore.QTransform()
        # self.cuboidTransform.setScale(10.0)
        # self.cuboidTransform.setTranslation(QVector3D(5.0, -4.0, 0.0))

        # self.cuboidMaterial = Qt3DExtras.QPhongAlphaMaterial()
        # self.cuboidMaterial.setDiffuse(QColor.fromRgb(120, 20, 20))
        # self.cuboidMaterial.setAlpha(0.5)

        # self.cuboidEntity = Qt3DCore.QEntity(self)
        # self.cuboidEntity.addComponent(self.cuboid)
        # self.cuboidEntity.addComponent(self.cuboidMaterial)
        # self.cuboidEntity.addComponent(self.cuboidTransform)

        # self.sphere = []
        # count = 100
        # for i in range(count):
        #    self.sphere.append(SphereEntity(self, QVector3D(i, i, i), QVector3D(0, 100 * i / count, 0)))

        points = np.array([[0, -10, 0],
                           [0, 10, 0],
                           [10, 10, 10],
                           [10, 10, 20]
                           ], dtype=np.float)

        # ssc = sscweb.SscWeb()
        # sv = ssc.get_orbit(product="mms1",
        #                    start_time="2020-10-10",
        #                    stop_time="2020-10-24",
        #                    coordinate_system='gse')

        # points = sv.data[::50, 0:3] / 10000

        # self.line = Line(points, QColor.fromRgb(0, 255, 0), self)

        # self.spheres = []
        # for p in points:
        #     print(p, p[0])
        #     self.spheres.append(Sphere(self, QVector3D(p[0], p[1], p[2]), 0.1))

        # self.plane = Plane(10, 10, QSize(2, 3), False, QColor.fromRgb(0, 255, 0), self)

        self.plane = Qt3DCore.QEntity(self)

        self.planeMesh = Qt3DExtras.QPlaneMesh()
        Qt3DRender.QGeometryRenderer(self.planeMesh).setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)
        self.planeTransform = Qt3DCore.QTransform()
        self.planeMaterial = Qt3DExtras.QPhongMaterial(self)

        self.planeMesh.setWidth(10)
        self.planeMesh.setHeight(10)

        self.planeMesh.setMeshResolution(QSize(10, 10))

        self.planeTransform.setTranslation(QVector3D(0, 0, 0))
        # self.planeMaterial.setDiffuse(QColor(150, 150, 150))
        # self.planeMaterial.setAmbient(QColor(150, 150, 150))

        self.plane.addComponent(self.planeMaterial)
        self.plane.addComponent(self.planeMesh)
        self.plane.addComponent(self.planeTransform)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    view = Qt3DExtras.Qt3DWindow()
    view.setTitle("3D PySide2")
    view.defaultFrameGraph().setClearColor(QColor(210, 210, 220))

    # scene = Scene()
    root = Qt3DCore.QEntity()

    e = []

    for i in range(-5, 6):
        for j in range(-5, 6):
            point = Point(QVector3D(i, j, 0))

            e += [point]

            point_transform = Qt3DCore.QTransform()
            point_transform.setTranslation(QVector3D(0, 0, 0))  # position

            e += [point_transform]

            # // this is my hacky way of setting point size
            # // the better way to do this is probably to create
            # // your own shader and then use QPointSize::SizeMode::Programmable
            # // that's for another journal...
            point_material = Qt3DExtras.QPhongMaterial()
            point_material.setAmbient(QColor(255, 0, 0))

            effect = point_material.effect()
            for t in effect.techniques():
                for rp in t.renderPasses():
                    pointSize = Qt3DRender.QPointSize()
                    pointSize.setSizeMode(Qt3DRender.QPointSize.SizeMode.Fixed)
                    pointSize.setValue(4.0)
                    rp.addRenderState(pointSize)
                    e += [pointSize]

            e += [point_material]

            entity = Qt3DCore.QEntity(root)
            entity.addComponent(point)
            entity.addComponent(point_transform)
            entity.addComponent(point_material)

            e += [entity]

            # self.e += [Sphere(self, QVector3D(i, j, 0), 0.1)]
            # self.e.append(selfSphere(self, QVector3D(i, j, 0), 0.1))

    # Camera
    camera = view.camera()
    camera.lens().setPerspectiveProjection(65.0, 16.0 / 9.0, 0.1, 100.0)
    camera.setPosition(QVector3D(-5, 10, -20.0))
    camera.setViewCenter(QVector3D(0, 0, 0))



#    # For camera controls
#    camController = Qt3DExtras.QOrbitCameraController(scene)
#    camController.setLinearSpeed(50.0)
#    camController.setLookSpeed(180.0)
#    camController.setCamera(camera)

    view.setRootEntity(root)
    view.show()

    sys.exit(app.exec_())
