
import Qt 4.7

Item {
    id: sleepTimerArea
    signal close

    MouseArea {
        anchors.fill: parent
        onClicked: sleepTimerArea.close()
    }
    Rectangle {
        color: "#" + config.background
        anchors.fill: parent
        opacity: .9
    }
    Text {
        text: shutdown_str
        y: config.font_size
        anchors.horizontalCenter: parent.horizontalCenter
        font.pixelSize: config.font_size * 1.5
        color: "#" + config.foreground
    }
    Rectangle {
        id: valuebar
        width: root.width / 2
        height: config.font_size * 3
        y: config.font_size * 3.5
        anchors.horizontalCenter: parent.horizontalCenter
        color: "#" + config.progress_bg_color

        MouseArea {
            anchors.fill: parent
            onClicked: { value.text = Math.round(Math.pow((1 + (mouseX / parent.width)), 10))
                         progress.width = mouseX
                       }
        }
        Rectangle {
            id: progress
            width: 0
            color: "#" + config.progress_color
            anchors {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
            }
        }
    }
    Text {
        id: value
        text: "1"
        anchors.centerIn: valuebar
        font.pixelSize: config.font_size * 1.5
        color: "#" + config.foreground
    }
    Rectangle {
        anchors.horizontalCenter: parent.horizontalCenter
        y: config.font_size * 7.5
        width: config.button_width
        height: config.button_height
        color: "#" + config.button_color
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            anchors.centerIn: parent
            smooth: true
            source: "apply.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { sleepTimerArea.close()
                         main.start_timed_shutdown(value.text)
                       }
        }
    }
}
