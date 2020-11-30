#!/usr/bin/env python3

import sys

import struct

import numpy as np

from PySide2.Qt3DExtras import Qt3DExtras
from PySide2.Qt3DCore import Qt3DCore
from PySide2.Qt3DRender import Qt3DRender

from PySide2.QtWidgets import (
    QApplication,
)

from PySide2.QtGui import (
    QVector3D,
    QColor,
)

from PySide2.QtCore import (
    QSize,
    QUrl,
)


def _createPlaneVertexData(w: float, h: float, resolution: QSize, mirrored: bool):
    assert resolution.width() > 1
    assert resolution.height() > 1

    nVerts = resolution.width() * resolution.height()

    # Populate a buffer with the interleaved per-vertex data with
    # vec3 pos, vec2 texCoord, vec3 normal, vec4 tangent

    elementSize = 3 + 2 + 3 + 4
    stride = elementSize * 4  # sizeof(float)

    # same, but with numpy
    ndata = np.empty((nVerts, elementSize), dtype=np.single)

    # x, y, z
    ndata[:, 0] = np.resize(np.linspace(-w / 2.0, w / 2.0, resolution.width()),
                            resolution.width() * resolution.height())
    ndata[:, 1] = 0.0
    ndata[:, 2] = np.repeat(np.linspace(-h / 2.0, h / 2.0, resolution.height()),
                            resolution.width())

    # texture coordinates
    ndata[:, 3] = np.resize(np.linspace(0.0, 1.0, resolution.width()),
                            resolution.width() * resolution.height())

    if mirrored:
        nv = np.linspace(1.0, 0.0, resolution.height())
    else:
        nv = np.linspace(0.0, 1.0, resolution.height())

    ndata[:, 4] = np.repeat(nv, resolution.width())

    # normal
    ndata[:, 5] = 0.0
    ndata[:, 6] = 1.0
    ndata[:, 7] = 0.0

    # tangent
    ndata[:, 8] = 1.0
    ndata[:, 9] = 0.0
    ndata[:, 10] = 0.0
    ndata[:, 11] = 1.0

    # ndata = np.array(data, dtype=np.single)
    bytes = ndata.tobytes()

    assert len(ndata.flatten()) == (nVerts * elementSize)
    assert len(ndata.tobytes()) == (nVerts * stride)

    return bytes


def _createPlaneIndexData(resolution: QSize):
    # Create the index data. 2 triangles per rectangular face
    faces = 2 * (resolution.width() - 1) * (resolution.height() - 1)
    indices = 3 * faces

    data = []
    for j in range(resolution.height() - 1):
        rowStartIndex = j * resolution.width()
        nextRowStartIndex = (j + 1) * resolution.width()

        for i in range(resolution.width() - 1):  # Iterate over x

            # Split quad into two triangles
            data.append(rowStartIndex + i)
            data.append(nextRowStartIndex + i)
            data.append(rowStartIndex + i + 1)

            data.append(nextRowStartIndex + i)
            data.append(nextRowStartIndex + i + 1)
            data.append(rowStartIndex + i + 1)

    bytes = np.array(data, dtype=np.int16).tobytes()

    assert len(data) == indices
    assert len(bytes) == (indices * 2)

    return bytes


class PlaneGeometry(Qt3DRender.QGeometry):
    def __init__(self, w: float, h: float, resolution: QSize, mirrored: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        positionAttribute = Qt3DRender.QAttribute(self)
        normalAttribute = Qt3DRender.QAttribute(self)
        texCoordAttribute = Qt3DRender.QAttribute(self)
        tangentAttribute = Qt3DRender.QAttribute(self)
        indexAttribute = Qt3DRender.QAttribute(self)

        vertexBuffer = Qt3DRender.QBuffer(self)
        indexBuffer = Qt3DRender.QBuffer(self)

        nVerts = resolution.width() * resolution.height()
        stride = (3 + 2 + 3 + 4) * 4  # sizeof(float);
        faces = 2 * (resolution.width() - 1) * (resolution.height() - 1)

        positionAttribute.setName(Qt3DRender.QAttribute.defaultPositionAttributeName())
        positionAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        positionAttribute.setVertexSize(3)
        positionAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        positionAttribute.setBuffer(vertexBuffer)
        positionAttribute.setByteStride(stride)
        positionAttribute.setCount(nVerts)

        texCoordAttribute.setName(Qt3DRender.QAttribute.defaultTextureCoordinateAttributeName())
        texCoordAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        texCoordAttribute.setVertexSize(2)
        texCoordAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        texCoordAttribute.setBuffer(vertexBuffer)
        texCoordAttribute.setByteStride(stride)
        texCoordAttribute.setByteOffset(3 * 4)
        texCoordAttribute.setCount(nVerts)

        normalAttribute.setName(Qt3DRender.QAttribute.defaultNormalAttributeName())
        normalAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        normalAttribute.setVertexSize(3)
        normalAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        normalAttribute.setBuffer(vertexBuffer)
        normalAttribute.setByteStride(stride)
        normalAttribute.setByteOffset(5 * 4)
        normalAttribute.setCount(nVerts)

        tangentAttribute.setName(Qt3DRender.QAttribute.defaultTangentAttributeName())
        tangentAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        tangentAttribute.setVertexSize(4)
        tangentAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        tangentAttribute.setBuffer(vertexBuffer)
        tangentAttribute.setByteStride(stride)
        tangentAttribute.setByteOffset(8 * 4)
        tangentAttribute.setCount(nVerts)

        indexAttribute.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        indexAttribute.setVertexBaseType(Qt3DRender.QAttribute.UnsignedShort)
        indexAttribute.setBuffer(indexBuffer)
        indexAttribute.setCount(faces * 3)  # Each primitive has 3 vertives

        vertexBuffer.setData(_createPlaneVertexData(w, h, resolution, mirrored))
        indexBuffer.setData(_createPlaneIndexData(resolution))

        self.addAttribute(positionAttribute)
        self.addAttribute(texCoordAttribute)
        self.addAttribute(normalAttribute)
        self.addAttribute(tangentAttribute)
        self.addAttribute(indexAttribute)


class Plane(Qt3DRender.QGeometryRenderer):
    def __init__(self, w: float, h: float, resolution: QSize, mirrored: bool = False, *args, **kwargs):
        super().__init__(*args, **kwargs)

        geometry = PlaneGeometry(w, h, resolution, mirrored, self)

        # self.setPrimitiveType(Qt3DRender.QGeometryRenderer.Points)
        # self.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)
        self.setGeometry(geometry)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    view = Qt3DExtras.Qt3DWindow()
    view.setTitle("3D PySide2")
    view.defaultFrameGraph().setClearColor(QColor(210, 210, 220))

    # scene = Scene()
    root = Qt3DCore.QEntity()

    e = []

    for i in range(2):
        plane = Qt3DCore.QEntity(root)
        # planeMesh = Qt3DExtras.QPlaneMesh()
        planeMesh = Plane(800, 419, QSize(100, 100), plane)
        # planeMesh.setWidth(10)
        # planeMesh.setHeight(10)

        planeTransform = Qt3DCore.QTransform(plane)
        planeTransform.setTranslation(QVector3D(0, i, 0))

        # and glue some texture onto our sphere
        loader = Qt3DRender.QTextureLoader(plane)
        loader.setSource(QUrl.fromLocalFile('/home/pmp/devel/upstream/qt3d/examples/qt3d/planets-qml/images/solarsystemscope/earthmap2k.jpg'))
        planeMaterial = Qt3DExtras.QTextureMaterial(plane)
        planeMaterial.setTexture(loader)

        # planeMaterial = Qt3DExtras.QPhongMaterial(plane)
        # planeMaterial.setDiffuse(QColor(150, 150, 150))

        # for t in planeMaterial.effect().techniques():
        #     for rp in t.renderPasses():
        #         pointSize = Qt3DRender.QPointSize(plane)
        #         pointSize.setSizeMode(Qt3DRender.QPointSize.SizeMode.Fixed)
        #         pointSize.setValue(2.0)
        #         rp.addRenderState(pointSize)

        plane.addComponent(planeMesh)
        plane.addComponent(planeTransform)
        plane.addComponent(planeMaterial)

    # Camera
    camera = view.camera()
    camera.lens().setPerspectiveProjection(65.0, 16.0 / 9.0, 0.1, 2000.0)
    camera.setPosition(QVector3D(0, 200, 1000.0))
    camera.setViewCenter(QVector3D(0, 0, 0))

    camController = Qt3DExtras.QOrbitCameraController(root)
    camController.setCamera(camera)

    view.setRootEntity(root)
    view.show()

    sys.exit(app.exec_())
