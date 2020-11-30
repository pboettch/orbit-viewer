#include <QGuiApplication>
#include <Qt3DCore/Qt3DCore>
#include <Qt3DExtras/Qt3DExtras>
#include <Qt3DRender/QPointSize>

#include "point.h"

int main(int argc, char *argv[])
{
	QGuiApplication a(argc, argv);

	Qt3DExtras::Qt3DWindow *view = new Qt3DExtras::Qt3DWindow();
	view->setTitle(QStringLiteral("3D Text CPP"));
	view->defaultFrameGraph()->setClearColor(QColor(210, 210, 220));

	auto root = new Qt3DCore::QEntity();

	{ // plane
		auto *plane = new Qt3DCore::QEntity(root);
		auto *planeMesh = new Qt3DExtras::QPlaneMesh();
		auto *planeTransform = new Qt3DCore::QTransform();
		auto *planeMaterial = new Qt3DExtras::QPhongMaterial(root);
		planeMesh->setWidth(10);
		planeMesh->setHeight(10);
		planeTransform->setTranslation(QVector3D(0, 0, 0));
		planeMaterial->setDiffuse(QColor(150, 150, 150));

		plane->addComponent(planeMaterial);
		plane->addComponent(planeMesh);
		plane->addComponent(planeTransform);
	}

    auto points_root = new Qt3DCore::QEntity(root);

	for (int i = -5; i < 6; i++) {
		for (int j = -5; j < 6; j++) {
			auto point_entity = new Qt3DCore::QEntity(points_root);
			auto point = new Point(QVector3D(i, j, 0));
			auto point_transform = new Qt3DCore::QTransform();
			auto point_material = new Qt3DExtras::QPhongMaterial();

			// this is my hacky way of setting point size
			// the better way to do this is probably to create
			// your own shader and then use QPointSize::SizeMode::Programmable
			// that's for another journal...
			auto effect = point_material->effect();
			for (auto t : effect->techniques()) {
				for (auto rp : t->renderPasses()) {
					auto pointSize = new Qt3DRender::QPointSize();
					pointSize->setSizeMode(Qt3DRender::QPointSize::SizeMode::Fixed);
					pointSize->setValue(4.0f);
					rp->addRenderState(pointSize);
				}
			}

			point_material->setAmbient(QColor(255, 0, 0));

			point_entity->addComponent(point);
			point_entity->addComponent(point_material);
			point_entity->addComponent(point_transform);
		}
	}

	{ // camera
		float aspect = static_cast<float>(view->screen()->size().width()) / view->screen()->size().height();
		Qt3DRender::QCamera *camera = view->camera();
		camera->lens()->setPerspectiveProjection(65.f, aspect, 0.1f, 100.f);
		camera->setPosition(QVector3D(0, 5, -10));
		camera->setViewCenter(QVector3D(0, 2, 0));

		auto *cameraController = new Qt3DExtras::QOrbitCameraController(root);
		cameraController->setCamera(camera);
	}

	view->setRootEntity(root);
	view->show();

	return a.exec();
}
