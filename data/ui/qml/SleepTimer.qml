
import QtQuick 1.1

Item {
    id: sleepTimerArea
    signal close

    MouseArea {
        anchors.fill: parent
        onClicked: sleepTimerArea.close()
    }
    Rectangle {
        color: themeController.background
        anchors.fill: parent
        opacity: .9
    }
    Text {
        text: shutdown_str
        y: config.font_size
        anchors.horizontalCenter: parent.horizontalCenter
        font.pixelSize: config.font_size * 1.5
        color: themeController.foreground
    }
    Rectangle {
        id: valuebar
        width: root.width / 2
        height: config.font_size * 3
        y: config.font_size * 3.5
        anchors.horizontalCenter: parent.horizontalCenter
        color: themeController.progress_bg_color

        MouseArea {
            anchors.fill: parent
            onClicked: { value.text = Math.round(Math.pow((1 + (mouseX / parent.width)), 10))
                         progress.width = mouseX
                       }
        }
        Rectangle {
            id: progress
            width: (Math.pow(5, 0.1) - 1) * parent.width
            color: themeController.progress_color
            anchors {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
            }
        }
    }
    Text {
        id: value
        text: "5"
        anchors.centerIn: valuebar
        font.pixelSize: config.font_size * 1.5
        color: themeController.foreground
    }
    AppButton {
        anchors.horizontalCenter: parent.horizontalCenter
        y: config.font_size * 7.5
        image: "artwork/apply.png"
        onClicked: { sleepTimerArea.close()
                     main.start_timed_shutdown(value.text)
                   }
    }
}
