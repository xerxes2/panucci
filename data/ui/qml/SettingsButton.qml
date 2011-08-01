
import Qt 4.7

Rectangle {
    id: settingsButton
    property bool checked: false
    property variant text: ""
    signal clicked
    anchors.horizontalCenter: parent.horizontalCenter
    color: checked ? themeController.progress_color : themeController.progress_bg_color
    width: parent.width / 2
    height: config.font_size * 4
    radius: config.button_radius
    smooth: true

    Text {
        anchors.centerIn: parent
        text: settingsButton.text
        font.pixelSize: config.font_size
        color: themeController.foreground
    }
    MouseArea {
        anchors.fill: parent
        onClicked: settingsButton.clicked()
    }
}
