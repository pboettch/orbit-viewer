#include <QVector3D>
#include <Qt3DRender/QBuffer>
#include <Qt3DRender/QGeometryRenderer>

class Point : public Qt3DRender::QGeometryRenderer
{
	Q_OBJECT
public:
	explicit Point(const QVector3D &position, Qt3DCore::QNode *parent = nullptr);
	~Point() {}
};

class PointGeometry : public Qt3DRender::QGeometry
{
	Q_OBJECT
public:
	explicit PointGeometry(const QVector3D &position, QNode *parent = nullptr);
	~PointGeometry() {}

	void updateVertices();
	void updateIndices();

	Qt3DRender::QBuffer *vertexBuffer;
	Qt3DRender::QBuffer *indexBuffer;
	Qt3DRender::QAttribute *positionAttribute;
	Qt3DRender::QAttribute *indexAttribute;
};

