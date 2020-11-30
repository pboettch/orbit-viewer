#!/usr/bin/env python3

import sys

from PySide2.QtWidgets import (
    QApplication,
)

from PySide2.QtGui import (
    QColor,
    QVector3D,
    QFontDatabase,
    QFont
)

from PySide2.Qt3DExtras import Qt3DExtras as q3dx
from PySide2.Qt3DCore import Qt3DCore as q3dc

if __name__ == '__main__':
    # Create the Qt Application
    app = QApplication(sys.argv)

    view = q3dx.Qt3DWindow()
    view.setTitle("3D Text CPP");
    view.defaultFrameGraph().setClearColor(QColor(210, 210, 220))

    root = q3dc.QEntity()

    # plane
    plane = q3dc.QEntity(root)
    planeMesh = q3dx.QPlaneMesh()
    planeTransform = q3dc.QTransform()
    planeMaterial = q3dx.QPhongMaterial(root)

    planeMesh.setWidth(10)
    planeMesh.setHeight(10)

    planeTransform.setTranslation(QVector3D(0, 0, 0))
    planeMaterial.setDiffuse(QColor(150, 150, 150))

    plane.addComponent(planeMaterial)
    plane.addComponent(planeMesh)
    plane.addComponent(planeTransform)

    # text

    i = 0

    text = q3dc.QEntity(root)

    textMaterial = q3dx.QPhongMaterial(text)
    textMaterial.setDiffuse(QColor(111, 150, 255))

    text.addComponent(textMaterial)

    texts = []
    for family in QFontDatabase().families():
        if not family.startswith('Liberation'):
            continue

        font = QFont(family, 32, -1, False)

        t = q3dc.QEntity(text)
        textTransform = q3dc.QTransform(t)
        textTransform.setTranslation(QVector3D(-2.45, i * .5, 0))
        textTransform.setScale(.2)

        textMesh = q3dx.QExtrudedTextMesh(t)
        textMesh.setDepth(.45)
        textMesh.setFont(font)
        textMesh.setText(family)

        t.addComponent(textMesh)
        t.addComponent(textTransform)

        text.add

        texts.append([text, textMesh, textTransform])

        i += 1



    # camera
    aspect = float(view.screen().size().width()) / view.screen().size().height()

    camera = view.camera()
    camera.lens().setPerspectiveProjection(65., aspect, 0.1, 100.)
    camera.setPosition(QVector3D(10, 5, 3))
    camera.setViewCenter(QVector3D(0, 5, 0))

    cameraController = q3dx.QOrbitCameraController(root)
    cameraController.setCamera(camera)





    view.setRootEntity(root)
    view.show()

    # Run the main Qt loop
    sys.exit(app.exec_())

"""
    auto *textMaterial = new Qt3DExtras::QPhongMaterial(root);
    { // text
        int i = 0;
        const QStringList fonts = QFontDatabase::families();

        for (const QString &family : fonts)
        {
            auto *text = new Qt3DCore::QEntity(root);
            auto *textMesh = new Qt3DExtras::QExtrudedTextMesh();

            auto *textTransform = new Qt3DCore::QTransform();
            QFont font(family, 32, -1, false);
            textTransform->setTranslation(QVector3D(-2.45f, i * .5f, 0));
            textTransform->setScale(.2f);
            textMesh->setDepth(.45f);
            textMesh->setFont(font);
            textMesh->setText(family);
            textMaterial->setDiffuse(QColor(111, 150, 255));

            text->addComponent(textMaterial);
            text->addComponent(textMesh);
            text->addComponent(textTransform);

            i++;
        }
    }


    view->setRootEntity(root);
    view->show();

    return a.exec();
}

"""
