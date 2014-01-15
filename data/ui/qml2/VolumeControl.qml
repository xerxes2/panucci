
import QtQuick 2.0

Item {
    id: volumeControlArea
    signal close
    property variant value: ""

    MouseArea {
        anchors.fill: parent
        onClicked: volumeControlArea.close()
    }
    Rectangle {
        color: themeController.background
        anchors.fill: parent
        opacity: .9
    }
    Text {
        text: volume_level_str
        y: config.font_size
        anchors.horizontalCenter: parent.horizontalCenter
        font.pixelSize: config.font_size * 1.5
        color: themeController.foreground
    }
    Rectangle {
        id: valuebar
        width: root.width / 1.5
        height: config.progress_height
        y: config.font_size * 3.5
        anchors.horizontalCenter: parent.horizontalCenter
        color: themeController.progress_bg_color

        MouseArea {
            anchors.fill: parent
            onClicked: { if (volumeControlArea.value != "None") {
                             volumeControlArea.value = Math.round((mouseX / parent.width) * 100)
                             main.set_volume_level(volumeControlArea.value)
                         }
                       }
        }
        Rectangle {
            id: progress
            width: volumeControlArea.value == "None" ? 0: valuebar.width * (volumeControlArea.value / 100)
            color: themeController.progress_color
            anchors {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
            }
        }
    }
    Text {
        text: volumeControlArea.value == "None" ? disabled_str: volumeControlArea.value
        anchors.centerIn: valuebar
        font.pixelSize: config.progress_height / 2
        color: themeController.foreground
    }
}
