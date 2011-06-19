
import Qt 4.7

Item {
    id: settingsArea
    signal close

    MouseArea {
        anchors.fill: parent
        onClicked: settingsArea.close()
    }
    Rectangle {
        color: "#" + config.background
        anchors.fill: parent
        opacity: .9
    }
    Flickable {
        width: root.width - config.button_width - config.button_border_width
        height: root.height
        contentWidth: root.width - config.button_width - config.button_border_width
        contentHeight: config.font_size * 44.5
        clip: true

        MouseArea {
            anchors.fill: parent
            onClicked: settingsArea.close()
        }
        Text {
            y: config.font_size
            anchors.horizontalCenter: parent.horizontalCenter
            text: main_window_str
            font.pixelSize: config.font_size * 1.5
            color: "#" + config.foreground
        }
        Rectangle {
            id: action_scrolling_labels_button
            property bool checked
            checked: action_scrolling_labels.checked
            y: config.font_size * 3.5
            anchors.horizontalCenter: parent.horizontalCenter
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            width: parent.width / 2
            height: config.font_size * 4
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_scrolling_labels.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { if (action_scrolling_labels_button.checked) {
                                 action_scrolling_labels_button.checked = false
                             }
                             else {
                                 action_scrolling_labels_button.checked = true
                             }
                           }
            }
        }
        Rectangle {
            id: action_lock_progress_button
            property bool checked
            checked: action_lock_progress.checked
            y: config.font_size * 8.5
            anchors.horizontalCenter: parent.horizontalCenter
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            width: parent.width / 2
            height: config.font_size * 4
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_lock_progress.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { if (action_lock_progress_button.checked) {
                                 action_lock_progress_button.checked = false
                             }
                             else {
                                 action_lock_progress_button.checked = true
                             }
                           }
            }
        }
        Rectangle {
            id: action_dual_action_button
            property bool checked
            checked: action_dual_action.checked
            y: config.font_size * 13.5
            anchors.horizontalCenter: parent.horizontalCenter
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            width: parent.width / 2
            height: config.font_size * 4
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_dual_action.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { if (action_dual_action_button.checked) {
                                 action_dual_action_button.checked = false
                             }
                             else {
                                 action_dual_action_button.checked = true
                             }
                           }
            }
        }
        Text {
            y: config.font_size * 19
            anchors.horizontalCenter: parent.horizontalCenter
            text: playback_str
            font.pixelSize: config.font_size * 1.5
            color: "#" + config.foreground
        }
        
        Rectangle {
            id: action_stay_at_end_button
            property bool checked
            checked: action_stay_at_end.checked
            y: config.font_size * 21.5
            anchors.horizontalCenter: parent.horizontalCenter
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            width: parent.width / 2
            height: config.font_size * 4
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_stay_at_end.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { if (action_stay_at_end_button.checked) {
                                 action_stay_at_end_button.checked = false
                             }
                             else {
                                 action_stay_at_end_button.checked = true
                             }
                           }
            }
        }
        Rectangle {
            id: action_seek_back_button
            property bool checked
            checked: action_seek_back.checked
            y: config.font_size * 26.5
            anchors.horizontalCenter: parent.horizontalCenter
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            width: parent.width / 2
            height: config.font_size * 4
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_seek_back.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { if (action_seek_back_button.checked) {
                                 action_seek_back_button.checked = false
                             }
                             else {
                                 action_seek_back_button.checked = true
                             }
                           }
            }
        }
        Rectangle {
            id: action_resume_all_button
            property bool checked
            checked: action_resume_all.checked
            y: config.font_size * 31.5
            anchors.horizontalCenter: parent.horizontalCenter
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            width: parent.width / 2
            height: config.font_size * 4
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_resume_all.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { if (action_resume_all_button.checked) {
                                 action_resume_all_button.checked = false
                             }
                             else {
                                 action_resume_all_button.checked = true
                             }
                           }
            }
        }
        Text {
            y: config.font_size * 37
            anchors.horizontalCenter: parent.horizontalCenter
            text: play_mode_str
            font.pixelSize: config.font_size * 1.5
            color: "#" + config.foreground
        }
        Rectangle {
            id: action_play_mode_all_button
            property bool checked
            checked: action_play_mode_all.checked
            y: config.font_size * 39.5
            x: parent.width / 25
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            width: parent.width / 5
            height: config.font_size * 4
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_play_mode_all.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { action_play_mode_all_button.checked = true
                             action_play_mode_single_button.checked = false
                             action_play_mode_random_button.checked = false
                             action_play_mode_repeat_button.checked = false
                           }
            }
        }
        Rectangle {
            id: action_play_mode_single_button
            property bool checked
            checked: action_play_mode_single.checked
            width: parent.width / 5
            height: config.font_size * 4
            y: config.font_size * 39.5
            x: (parent.width / 25 * 2) + width
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_play_mode_single.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { action_play_mode_all_button.checked = false
                             action_play_mode_single_button.checked = true
                             action_play_mode_random_button.checked = false
                             action_play_mode_repeat_button.checked = false
                           }
            }
        }
        Rectangle {
            id: action_play_mode_random_button
            property bool checked
            checked: action_play_mode_random.checked
            width: parent.width / 5
            height: config.font_size * 4
            y: config.font_size * 39.5
            x: (parent.width / 25 * 3) + (width * 2)
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_play_mode_random.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { action_play_mode_all_button.checked = false
                             action_play_mode_single_button.checked = false
                             action_play_mode_random_button.checked = true
                             action_play_mode_repeat_button.checked = false
                           }
            }
        }
        Rectangle {
            id: action_play_mode_repeat_button
            property bool checked
            checked: action_play_mode_repeat.checked
            width: parent.width / 5
            height: config.font_size * 4
            y: config.font_size * 39.5
            x: (parent.width / 25 * 4) + (width * 3)
            color: checked ? "#" + config.progress_color : "#" + config.progress_bg_color
            radius: config.button_radius
            smooth: true

            Text {
                anchors.centerIn: parent
                text: action_play_mode_repeat.text
                font.pixelSize: config.font_size
                color: "#" + config.foreground
            }
            MouseArea {
                anchors.fill: parent
                onClicked: { action_play_mode_all_button.checked = false
                             action_play_mode_single_button.checked = false
                             action_play_mode_random_button.checked = false
                             action_play_mode_repeat_button.checked = true
                           }
            }
        }
    }
    Rectangle {
        x: root.width - config.button_width - config.button_border_width
        y: root.height - config.button_height
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
            onClicked: { var i=0
                         for (i=0;i<settingsArea.actions.length;i++) {
                             if (settingsArea.actions[i].checked != settingsArea.buttons[i].checked)
                                 settingsArea.actions[i].trigger()
                         }
                         settingsArea.close()
                       }
        }
    }
    property variant actions: [action_scrolling_labels, action_lock_progress,
            action_dual_action, action_stay_at_end, action_seek_back,
            action_resume_all,
            action_play_mode_all, action_play_mode_single,
            action_play_mode_random, action_play_mode_repeat]
    property variant buttons: [action_scrolling_labels_button, action_lock_progress_button,
            action_dual_action_button, action_stay_at_end_button, action_seek_back_button,
            action_resume_all_button,
            action_play_mode_all_button, action_play_mode_single_button,
            action_play_mode_random_button, action_play_mode_repeat_button]
    onClose: { var i=0
               for (i=0;i<settingsArea.actions.length;i++) {
                   settingsArea.buttons[i].checked = settingsArea.actions[i].checked
               }
             }
}
