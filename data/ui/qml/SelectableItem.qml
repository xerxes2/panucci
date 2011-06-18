
import Qt 4.7

Item {
    id: selectableItem
    signal selected(variant item)
    signal contextMenu(variant item)

    height: config.font_size * 5
    width: parent.width

    Rectangle {
        id: highlight
        opacity: mouseArea.pressed?.5:0
        color: "#" + config.progress_color
        anchors.fill: parent

        Behavior on opacity { NumberAnimation { duration: 150 } }
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
        onPressAndHold: selectableItem.contextMenu(modelData)
    }
}
