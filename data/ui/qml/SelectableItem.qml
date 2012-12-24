
import QtQuick 1.1

Item {
    id: selectableItem
    signal selected(variant item)
    signal contextMenu(variant item)

    height: config.font_size * 4.5
    width: parent.width

    Rectangle {
        id: highlight
        opacity: mouseArea.pressed?.5:0
        color: themeController.highlight
        anchors.fill: parent

        Behavior on opacity { NumberAnimation { duration: 500 } }
    }

    MouseArea {
        id: mouseArea
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        anchors.fill: parent
        onClicked: {
            if (mouse.button == Qt.LeftButton) {
                selectableItem.selected(modelData)
            } else if (mouse.button == Qt.RightButton) {
                selectableItem.contextMenu(modelData)
            }
        }
        //onPressAndHold: selectableItem.contextMenu(modelData)
    }
}
