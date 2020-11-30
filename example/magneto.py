#!/usr/bin/env python3

import sys

from astropy.constants import R_earth

from space.models.planetary import formisano1979, mp_formisano1979, bs_formisano1979

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

from orbit_viewer.geometries.callback import SphericalModelRenderer
from orbit_viewer.geometries.line import LineRenderer

if __name__ == "__main__":
    app = QApplication(sys.argv)

    view = Qt3DExtras.Qt3DWindow()
    view.setTitle("3D PySide2")
    view.defaultFrameGraph().setClearColor(QColor(210, 210, 220))

    # scene = Scene()
    root = Qt3DCore.QEntity()

    ms = Qt3DCore.QEntity(root)
    msr = SphericalModelRenderer(np.pi * 0.8, 2 * np.pi, mp_formisano1979, 30, 15, ms)
    # msr.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)
    ms.addComponent(msr)

    bs = Qt3DCore.QEntity(root)
    bsr = SphericalModelRenderer(np.pi * 0.75, 2 * np.pi, bs_formisano1979, 10, 20, bs)
    bsr.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)
    # bsr.setPrimitiveType(Qt3DRender.QGeometryRenderer.Points)
    bs.addComponent(bsr)

    color = [QColor.fromRgb(100, 20, 0),
             QColor.fromRgb(20, 100, 0)]
    i = 0
    for e in [ms, bs]:
        material = Qt3DExtras.QPhongAlphaMaterial(e)
        # material = Qt3DExtras.QPhongMaterial(e)
        e.addComponent(material)

        for t in material.effect().techniques():
            for rp in t.renderPasses():
                pointSize = Qt3DRender.QPointSize(rp)

                pointSize.setSizeMode(Qt3DRender.QPointSize.SizeMode.Fixed)
                pointSize.setValue(5.0)
                rp.addRenderState(pointSize)

                lineWidth = Qt3DRender.QLineWidth(rp)
                lineWidth.setValue(2000)
                lineWidth.setSmooth(True)
                rp.addRenderState(lineWidth)

                cullFace = Qt3DRender.QCullFace(rp)
                # cullFace.setMode(Qt3DRender.QCullFace.Front)
                cullFace.setMode(Qt3DRender.QCullFace.NoCulling)
                rp.addRenderState(cullFace)

        material.setDiffuse(color[i])
        # material.setAlpha(1)
        i += 1


    traj_ent = Qt3DCore.QEntity(root)
    # traj_ent = Qt3DCore.QEntity()

    if 0:
        X = np.linspace(-200, 200, 100).flatten()
        traj = LineRenderer(X, X, X, 0, traj_ent)

    else:
        from spwc import sscweb
        ssc = sscweb.SscWeb()
        sv = ssc.get_orbit(product="mms1",
                           start_time="2020-10-10",
                           stop_time="2020-10-24",
                           coordinate_system='gse')
        traj = LineRenderer(sv.data[::10, 0] / R_earth.to('km').value,
                            sv.data[::10, 1] / R_earth.to('km').value,
                            sv.data[::10, 2] / R_earth.to('km').value,
                            0,
                            traj_ent)

    traj.setPrimitiveType(Qt3DRender.QGeometryRenderer.LineStrip)
    traj_ent.addComponent(traj)

    material = Qt3DExtras.QPhongMaterial(traj_ent)
    material.setDiffuse(QColor(50, 0, 0))
    traj_ent.addComponent(material)

    def f(root, x, y, z):
        axis_ent = Qt3DCore.QEntity(root)

        axis = LineRenderer(x, y, z, 0, axis_ent)
        axis.setPrimitiveType(Qt3DRender.QGeometryRenderer.Lines)
        axis_ent.addComponent(axis)

        material = Qt3DExtras.QPhongMaterial(axis_ent)
        material.setDiffuse(QColor(50, 0, 0))
        axis_ent.addComponent(material)

    v = np.array([0, 20])
    n = np.array([0, 0])

    # f(root, v, n, n)
    # f(root, n, v, n)
    # f(root, n, n, v)

    # Camera
    camera = view.camera()
    camera.lens().setPerspectiveProjection(65.0, 16.0 / 9.0, 0.1, 200.0)
    camera.setPosition(QVector3D(0, 50, 50.0))
    camera.setViewCenter(QVector3D(0, 0, 0))

    camController = Qt3DExtras.QOrbitCameraController(root)
    camController.setCamera(camera)

    light_entity = Qt3DCore.QEntity(camera)
    light = Qt3DRender.QPointLight(light_entity)
    light.setColor("white")
    light.setIntensity(1)
    light_entity.addComponent(light)

    view.setRootEntity(root)
    view.show()

    sys.exit(app.exec_())
