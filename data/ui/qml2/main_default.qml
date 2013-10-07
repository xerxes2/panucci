
import QtQuick 2.0

Item {
    id: rootWindow
    property variant root: mainObject
    width: config.main_width
    height: config.main_height

    Main {
        id: mainObject
        anchors.fill: parent
    }
}
