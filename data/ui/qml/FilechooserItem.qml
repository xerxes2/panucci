
import QtQuick 1.1

Item {
    id: filechooserItem
    height: config.font_size * 3
    width: parent.width
    signal selected()

    MouseArea {
        id: mouseArea
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        anchors.fill: parent
        onClicked: {
            if (mouse.button == Qt.LeftButton) {
                filechooserItem.selected()
            }
        }
    }
}
