
import QtQuick 2.0

Rectangle {
    id: settingsButtonSmall
    property bool checked: false
    property variant text: ""
    signal clicked(variant button)
    color: checked ? themeController.progress_color : themeController.progress_bg_color
    width: parent.width / 5
    height: config.font_size * 4
    radius: config.button_radius
    smooth: true

    Text {
        anchors.centerIn: parent
        text: settingsButtonSmall.text
        font.pixelSize: config.font_size
        color: themeController.foreground
    }
    MouseArea {
        anchors.fill: parent
        onClicked: settingsButtonSmall.clicked(settingsButtonSmall)
    }
}
