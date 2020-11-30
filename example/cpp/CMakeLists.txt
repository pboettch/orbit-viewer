cmake_minimum_required(VERSION 3.14)
project(test-qt3d LANGUAGES CXX)

set(CMAKE_INCLUDE_CURRENT_DIR ON)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

find_package(Qt5 COMPONENTS Core)
find_package(Qt5 COMPONENTS Gui)
find_package(Qt5 COMPONENTS 3DCore)
find_package(Qt5 COMPONENTS 3DRender)
find_package(Qt5 COMPONENTS 3DExtras)

add_executable(points
    point.cpp point-main.cpp
)

target_link_libraries(points PUBLIC
    Qt::3DCore
    Qt::3DExtras
    Qt::3DRender
    Qt::Core
    Qt::Gui
)
