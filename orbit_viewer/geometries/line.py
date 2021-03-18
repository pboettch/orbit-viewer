import numpy as np

from PySide2.Qt3DRender import Qt3DRender


def _create_line_data(points: np.array):
    assert points.shape[0] == 3
    return points.T.astype(np.single).tobytes(), points.shape[1], 3 * 4


def _create_line_index_data(count: int):
    assert count < 2 ** 16
    return np.arange(0, count, dtype=np.uint16).tobytes(), count


class SimpleLineGeometry(Qt3DRender.QGeometry):
    def __init__(self, x: np.array, y: np.array, z: np.array, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if len(x.shape) != 1 and x.shape != y.shape != z.shape:
            raise ValueError('dimension arrays must have the same dimension and be a 1d-vector')

        # position vertices (start and end)
        data, vertex_count, stride = _create_line_data(np.array((x, y, z)))

        assert len(data) == (vertex_count * stride)

        buffer = Qt3DRender.QBuffer(self)
        buffer.setData(data)

        position_attribute = Qt3DRender.QAttribute(self)
        position_attribute.setName(Qt3DRender.QAttribute.defaultPositionAttributeName())
        position_attribute.setVertexBaseType(Qt3DRender.QAttribute.Float)
        position_attribute.setVertexSize(3)
        position_attribute.setAttributeType(Qt3DRender.QAttribute.VertexAttribute)
        position_attribute.setBuffer(buffer)
        position_attribute.setByteStride(stride)
        position_attribute.setCount(vertex_count)
        self.addAttribute(position_attribute)

        # connectivity between vertices
        index_data, indices = _create_line_index_data(len(x))
        assert len(index_data) == indices * 2

        index_buffer = Qt3DRender.QBuffer(self)
        index_buffer.setData(index_data)

        index_attribute = Qt3DRender.QAttribute(self)
        index_attribute.setVertexBaseType(Qt3DRender.QAttribute.UnsignedShort)
        index_attribute.setAttributeType(Qt3DRender.QAttribute.IndexAttribute)
        index_attribute.setBuffer(index_buffer)
        index_attribute.setCount(indices)
        self.addAttribute(index_attribute)


class LineRenderer(Qt3DRender.QGeometryRenderer):
    def __init__(self, x: np.array, y: np.array, z: np.array, r: float, *args, **kwargs):
        super().__init__(*args, **kwargs)

        assert r >= 0

        if r == 0:
            geometry = SimpleLineGeometry(x, y, z, self)
            self.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)

        else:
            raise NotImplementedError('pipelines are not implemented yet')
        self.setGeometry(geometry)
