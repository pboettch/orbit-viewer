from typing import Callable

import numpy as np

from PySide2.Qt3DRender import Qt3DRender

from astropy.constants import R_earth


def _create_spherical_vertex_data(phi_range: float, theta_range: float,
                                  model: Callable,
                                  rings: int, slices: int):
    assert rings > 0
    assert slices > 2

    vert_count = rings * slices
    vert_count += 1  # top point

    print('vertices', vert_count)

    # vec3 pos, vec2 texCoord (normal == pos), tangent TODO
    element_size = 3 + 2 + 3  # + 4

    stride = element_size * 4  # sizeof(float)

    data = np.empty((element_size, vert_count), dtype=np.single)

    # top point
    data[0, 0], data[1, 0], data[2, 0] = model(0, 0)

    ph_1d = np.linspace(0, phi_range, slices, endpoint=False)
    th_1d = np.linspace(0, theta_range, rings + 1)[1:]

    th, ph = np.meshgrid(th_1d, ph_1d, indexing='ij')

    data[0, 1:], data[1, 1:], data[2, 1:] = model(th.flatten(), ph.flatten())

    data[0] *= 6.3
    data[1] *= 6.3
    data[2] *= 6.3

    data[3][1:] = np.resize(np.linspace(0.0, 1.0, rings), rings * slices)

    # texture coordinates
    # if mirrored:
    # nv = np.linspace(1.0, 0.0, slices)
    # else:
    nv = np.linspace(0.0, 1.0, slices)

    data[4][1:] = np.repeat(nv, rings)

    # normal https://stackoverflow.com/questions/29661574/normalize-numpy-array-columns-in-pytho
    # data[5:8] = data[0:3] / np.abs(data[0:3]).max(axis=0)
    data[5:8] = -data[0:3] / np.abs(data[0:3]).max(axis=0)
    #
    # tangent TODO - orthogonal to the normal
    # data[8] = 1.0
    # data[9] = 0.0
    # data[10] = 0.0
    # data[11] = 1.0

    raw = data.T.tobytes()

    assert len(data.flatten()) == (vert_count * element_size)
    assert len(raw) == (vert_count * stride)

    return raw, vert_count, stride


def _create_spherical_index_data(rings: int, slices: int):
    faces = (slices * 2) * (rings - 1)  # two tris per slice, for all rings w/o top
    faces += slices  # tris for top

    indices = faces * 3
    assert indices < 65536

    index = np.empty(indices, dtype=np.uint16)

    # top cap
    first_ring_vertex = 1
    last_top_index = slices * 3

    index[0:last_top_index + 0:3] = np.arange(first_ring_vertex, slices + 1)
    index[1:last_top_index + 1:3] = 0
    index[2:last_top_index + 2:3] = np.concatenate([np.arange(first_ring_vertex + 1, slices + 1), [first_ring_vertex]])

    # ring-part - split the quad into two triangles
    ring_start_index = last_top_index

    offset = ring_start_index
    ringStartIndex = 1
    nextRingStartIndex = 1

    for i in range(0, rings - 1):
        nextRingStartIndex += slices

        for j in range(0, slices):
            index[offset + 0] = ringStartIndex + j
            index[offset + 1] = ringStartIndex + j + 1
            index[offset + 2] = nextRingStartIndex + j
            index[offset + 3] = nextRingStartIndex + j
            index[offset + 4] = ringStartIndex + j + 1
            index[offset + 5] = nextRingStartIndex + j + 1

            offset += 6

        # fix last triangle indices to use indices of the same ring
        index[offset - 5] = ringStartIndex
        index[offset - 2] = ringStartIndex
        index[offset - 1] = nextRingStartIndex

        ringStartIndex += slices

    bytes = np.array(index, dtype=np.int16).tobytes()

    assert len(index) == indices
    assert len(bytes) == (indices * 2)

    return bytes, faces, indices


class SphericalModelGeometry(Qt3DRender.QGeometry):
    """
    A Spherical Model geometry.

    Takes a callback function which returns the cartesian coordinate receiving thetha-phy-angles.
    """

    def __init__(self, theta_range: float, phi_range: float, model_callback: Callable, rings: int, slices: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        data, vertex_count, stride = _create_spherical_vertex_data(theta_range, phi_range, model_callback, rings,
                                                                   slices)

        vertexBuffer = Qt3DRender.QBuffer(self)
        vertexBuffer.setData(data)

        positionAttribute = Qt3DRender.QAttribute(self)
        positionAttribute.setName(Qt3DRender.QAttribute.defaultPositionAttributeName())
        positionAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        positionAttribute.setVertexSize(3)
        positionAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        positionAttribute.setBuffer(vertexBuffer)
        positionAttribute.setByteStride(stride)
        positionAttribute.setCount(vertex_count)
        self.addAttribute(positionAttribute)

        texCoordAttribute = Qt3DRender.QAttribute(self)
        texCoordAttribute.setName(Qt3DRender.QAttribute.defaultTextureCoordinateAttributeName())
        texCoordAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        texCoordAttribute.setVertexSize(2)
        texCoordAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        texCoordAttribute.setBuffer(vertexBuffer)
        texCoordAttribute.setByteStride(stride)
        texCoordAttribute.setByteOffset(3 * 4)
        texCoordAttribute.setCount(vertex_count)
        self.addAttribute(texCoordAttribute)

        normalAttribute = Qt3DRender.QAttribute(self)
        normalAttribute.setName(Qt3DRender.QAttribute.defaultNormalAttributeName())
        normalAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        normalAttribute.setVertexSize(3)
        normalAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        normalAttribute.setBuffer(vertexBuffer)
        normalAttribute.setByteStride(stride)
        normalAttribute.setByteOffset(5 * 4)  # xyz of a spherical model is also the normal (not normalized though)
        normalAttribute.setCount(vertex_count)
        self.addAttribute(normalAttribute)

        # tangentAttribute = Qt3DRender.QAttribute(self)
        # tangentAttribute.setName(Qt3DRender.QAttribute.defaultTangentAttributeName())
        # tangentAttribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        # tangentAttribute.setVertexSize(4)
        # tangentAttribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        # tangentAttribute.setBuffer(vertexBuffer)
        # tangentAttribute.setByteStride(stride)
        # tangentAttribute.setByteOffset(8 * 4)
        # tangentAttribute.setCount(nVerts)
        # self.addAttribute(tangentAttribute)

        index_data, _, indices = _create_spherical_index_data(rings, slices)

        indexBuffer = Qt3DRender.QBuffer(self)
        indexBuffer.setData(index_data)

        indexAttribute = Qt3DRender.QAttribute(self)
        indexAttribute.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        indexAttribute.setVertexBaseType(Qt3DRender.QAttribute.UnsignedShort)
        indexAttribute.setBuffer(indexBuffer)
        indexAttribute.setCount(indices)  # Each primitive has 3 vertices
        self.addAttribute(indexAttribute)


class SphericalModelRenderer(Qt3DRender.QGeometryRenderer):
    """
    A Spherical Model geometry renderer. See SphericalModelGeometry for more information concerning the parameters
    """

    def __init__(self, theta_range: float, phi_range: float, model: Callable, rings: int, slices: int,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        geometry = SphericalModelGeometry(theta_range, phi_range, model, rings, slices, self)
        self.setGeometry(geometry)
