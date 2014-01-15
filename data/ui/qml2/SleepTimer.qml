
import QtQuick 2.0

Item {
    id: sleepTimerArea
    signal close
    property variant mode: 0
    
    function timer_callback() {
        var _int_x
        var _int_v
        _int_v = value.text - 1
        value.text = _int_v
        _int_x = Math.round((Math.pow(_int_v, 0.1) - 1) * valuebar.width)
        if (_int_v == 1) {
            progress.width = 0.04 * valuebar.width
        }
        else {
            progress.width = _int_x
        }
        if (_int_v == 0)
            action_quit.trigger()
    }
    
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
        width: Math.round(root.width / 1.5)
        height: config.progress_height
        y: config.font_size * 3.5
        anchors.horizontalCenter: parent.horizontalCenter
        color: themeController.progress_bg_color

        MouseArea {
            anchors.fill: parent
            onClicked: { value.text = Math.round(Math.pow((1 + (mouseX / parent.width)), 10))
                         if (value.text == 1) {
                             progress.width = 0.04 * parent.width
                         }
                         else {
                             progress.width = mouseX
                         }
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
        font.pixelSize: config.progress_height / 2
        color: themeController.foreground
    }
    AppButton {
        id: shutdownButton
        anchors.horizontalCenter: parent.horizontalCenter
        y: valuebar.y + valuebar.height + config.font_size
        image: "artwork/media-playback-start.png"
        onClicked: { //sleepTimerArea.close()
                     if (mode == 0) {
                       mode = 1
                       shutdownButton.image = "artwork/media-playback-pause.png"
                       timer.start()
                     }
                     else {
                       mode = 0
                       shutdownButton.image = "artwork/media-playback-start.png"
                       timer.stop()
                     }
                   }
    }
    Timer {
         id: timer
         interval: 60000
         running: false
         repeat: true
         onTriggered: timer_callback()
    }
}
