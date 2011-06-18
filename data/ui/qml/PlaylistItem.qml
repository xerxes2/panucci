
import Qt 4.7

Item {
    id: playlistItem
    height: config.font_size * 3
    width: parent.width
    signal selected()

    MouseArea {
        id: mouseArea
        acceptedButtons: Qt.LeftButton | Qt.RightButton
        anchors.fill: parent
        onClicked: {
            if (mouse.button == Qt.LeftButton) {
                playlistItem.selected()
            }
        }
    }
}
