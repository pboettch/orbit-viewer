#include "point.h"

#include <Qt3DRender/QAttribute>

using namespace Qt3DRender;

Point::Point(const QVector3D &position, QNode *parent)
    : QGeometryRenderer(parent)
{
	PointGeometry *geometry = new PointGeometry(position, this);

	// tell OpenGL to expect a point primtiive
	// https://www.khronos.org/opengl/wiki/Primitive#Point_primitives
	setPrimitiveType(PrimitiveType::Points);
	QGeometryRenderer::setGeometry(geometry);
}

namespace
{
// set up a vertex buffer with our single vec3 position
QByteArray createPointVertexData(QVector3D position)
{
	const int nVerts = 1;
	const quint32 stride = 3 * sizeof(float);
	// create  a new buffer
	QByteArray bufferBytes;
	// set buffer size to number of vertices
	// we're only drawing one point, so we only have one
	// vec3 representing the position of our point
	bufferBytes.resize(stride * nVerts);

	// tell c++ to interpret this buffer as float so
	// we can use the next few lines to fill it
	float *fptr = reinterpret_cast<float *>(bufferBytes.data());

	*fptr++ = position.x();
	*fptr++ = position.y();
	*fptr++ = position.z();

	return bufferBytes;
}

// set up an index buffer telling OpenGL
// to render our single point
QByteArray createPointIndexData()
{
	QByteArray indexBytes;

	indexBytes.resize(1 * sizeof(quint16));
	quint16 *indexPtr = reinterpret_cast<quint16 *>(indexBytes.data());

	*indexPtr++ = 0;

	return indexBytes;
}
} // namespace

PointGeometry::PointGeometry(const QVector3D &position, QNode *parent)
    : QGeometry(parent)
{
	positionAttribute = new QAttribute();
	indexAttribute = new QAttribute();
	vertexBuffer = new Qt3DRender::QBuffer();
	indexBuffer = new Qt3DRender::QBuffer();

	const int nVerts = 3;
	const int stride = 0; // since the vertices are "side by side" in the buffer

	// this ultimately ends up configuring the OpenGL vertex array object
	// https://www.khronos.org/opengl/wiki/Vertex_Specification
	// this tells Qt3D / OpenGL to read the data from the buffer,
	// passing the 3 floats into the gl_Position parameter
	// on our shader (in this case the Qt3D default shader)
	positionAttribute->setName(QAttribute::defaultPositionAttributeName());
	positionAttribute->setVertexBaseType(QAttribute::Float);
	positionAttribute->setVertexSize(3);
	positionAttribute->setAttributeType(QAttribute::VertexAttribute);
	positionAttribute->setBuffer(vertexBuffer);
	positionAttribute->setByteStride(stride);
	positionAttribute->setCount(nVerts);

	indexAttribute->setAttributeType(QAttribute::IndexAttribute);
	indexAttribute->setVertexBaseType(QAttribute::UnsignedShort);
	indexAttribute->setBuffer(indexBuffer);

	// Each primitive has 3 vertives
	indexAttribute->setCount(1);

	vertexBuffer->setData(createPointVertexData(position));
	indexBuffer->setData(createPointIndexData());

	addAttribute(positionAttribute);
	addAttribute(indexAttribute);
}
