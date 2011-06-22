
import Qt 4.7

Item {
    id: settingsArea
    signal close

    MouseArea {
        anchors.fill: parent
        onClicked: settingsArea.close()
    }
    Rectangle {
        color: themeController.background
        anchors.fill: parent
        opacity: .9
    }
    Flickable {
        width: root.width - config.button_width - config.button_border_width
        height: root.height
        contentWidth: root.width - config.button_width - config.button_border_width
        contentHeight: config.font_size * 52.5
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
            color: themeController.foreground
        }
        SettingsButton {
            id: action_scrolling_labels_button
            checked: action_scrolling_labels.checked
            y: config.font_size * 3.5
            text: action_scrolling_labels.text
            onClicked: { if (action_scrolling_labels_button.checked) {
                             action_scrolling_labels_button.checked = false
                         }
                         else {
                             action_scrolling_labels_button.checked = true
                         }
            }
        }
        SettingsButton {
            id: action_lock_progress_button
            checked: action_lock_progress.checked
            y: config.font_size * 8.5
            text: action_lock_progress.text
            onClicked: { if (action_lock_progress_button.checked) {
                             action_lock_progress_button.checked = false
                         }
                         else {
                             action_lock_progress_button.checked = true
                         }
            }
        }
        SettingsButton {
            id: action_dual_action_button
            checked: action_dual_action.checked
            y: config.font_size * 13.5
            text: action_dual_action.text
            onClicked: { if (action_dual_action_button.checked) {
                             action_dual_action_button.checked = false
                         }
                         else {
                             action_dual_action_button.checked = true
                         }
            }
        }
        Text {
            y: config.font_size * 19
            anchors.horizontalCenter: parent.horizontalCenter
            text: playback_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
        SettingsButton {
            id: action_stay_at_end_button
            checked: action_stay_at_end.checked
            y: config.font_size * 21.5
            text: action_stay_at_end.text
            onClicked: { if (action_stay_at_end_button.checked) {
                             action_stay_at_end_button.checked = false
                         }
                         else {
                             action_stay_at_end_button.checked = true
                         }
            }
        }
        SettingsButton {
            id: action_seek_back_button
            checked: action_seek_back.checked
            y: config.font_size * 26.5
            text: action_seek_back.text
            onClicked: { if (action_seek_back_button.checked) {
                             action_seek_back_button.checked = false
                         }
                         else {
                             action_seek_back_button.checked = true
                         }
            }
        }
        SettingsButton {
            id: action_resume_all_button
            checked: action_resume_all.checked
            y: config.font_size * 31.5
            text: action_resume_all.text
            onClicked: { if (action_resume_all_button.checked) {
                             action_resume_all_button.checked = false
                         }
                         else {
                             action_resume_all_button.checked = true
                         }
            }
        }
        Text {
            y: config.font_size * 37
            anchors.horizontalCenter: parent.horizontalCenter
            text: play_mode_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
        SettingsButtonSmall {
            id: action_play_mode_all_button
            checked: action_play_mode_all.checked
            y: config.font_size * 39.5
            x: parent.width / 25
            text: action_play_mode_all.text
            onClicked: { action_play_mode_all_button.checked = true
                         action_play_mode_single_button.checked = false
                         action_play_mode_random_button.checked = false
                         action_play_mode_repeat_button.checked = false
           }
        }
        SettingsButtonSmall {
            id: action_play_mode_single_button
            checked: action_play_mode_single.checked
            width: parent.width / 5
            height: config.font_size * 4
            y: config.font_size * 39.5
            x: (parent.width / 25 * 2) + width
            text: action_play_mode_single.text
            onClicked: { action_play_mode_all_button.checked = false
                         action_play_mode_single_button.checked = true
                         action_play_mode_random_button.checked = false
                         action_play_mode_repeat_button.checked = false
            }
        }
        SettingsButtonSmall {
            id: action_play_mode_random_button
            checked: action_play_mode_random.checked
            width: parent.width / 5
            height: config.font_size * 4
            y: config.font_size * 39.5
            x: (parent.width / 25 * 3) + (width * 2)
            text: action_play_mode_random.text
            onClicked: { action_play_mode_all_button.checked = false
                         action_play_mode_single_button.checked = false
                         action_play_mode_random_button.checked = true
                         action_play_mode_repeat_button.checked = false
            }
        }
        SettingsButtonSmall {
            id: action_play_mode_repeat_button
            checked: action_play_mode_repeat.checked
            width: parent.width / 5
            height: config.font_size * 4
            y: config.font_size * 39.5
            x: (parent.width / 25 * 4) + (width * 3)
            text: action_play_mode_repeat.text
            onClicked: { action_play_mode_all_button.checked = false
                         action_play_mode_single_button.checked = false
                         action_play_mode_random_button.checked = false
                         action_play_mode_repeat_button.checked = true
            }
        }
        Text {
            y: config.font_size * 45
            anchors.horizontalCenter: parent.horizontalCenter
            text: theme_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
        SettingsButtonSmall {
            id: theme_black
            y: config.font_size * 47.5
            x: parent.width / 25
            text: "Black "
            checked: config.theme + " " == text.toLowerCase() ? true : false
            onClicked: { theme_black.checked = true
                         theme_blue.checked = false
                         theme_pink.checked = false
                         theme_custom.checked = false
                         themeController.set_theme(text)
            }
        }
        SettingsButtonSmall {
            id: theme_blue
            y: config.font_size * 47.5
            x: (parent.width / 25 * 2) + width
            text: "Blue "
            checked: config.theme + " " == text.toLowerCase() ? true : false
            onClicked: { theme_black.checked = false
                         theme_blue.checked = true
                         theme_pink.checked = false
                         theme_custom.checked = false
                         themeController.set_theme(text)
            }
        }
        SettingsButtonSmall {
            id: theme_pink
            y: config.font_size * 47.5
            x: (parent.width / 25 * 3) + (width * 2)
            text: "Pink "
            checked: config.theme + " " == text.toLowerCase() ? true : false
            onClicked: { theme_black.checked = false
                         theme_blue.checked = false
                         theme_pink.checked = true
                         theme_custom.checked = false
                         themeController.set_theme(text)
            }
        }
        SettingsButtonSmall {
            id: theme_custom
            y: config.font_size * 47.5
            x: (parent.width / 25 * 4) + (width * 3)
            text: "Custom"
            checked: config.theme + " " == text.toLowerCase() ? true : false
            onClicked: { theme_black.checked = false
                         theme_blue.checked = false
                         theme_pink.checked = false
                         theme_custom.checked = true
                         themeController.set_theme(text)
            }
        }
    }
    AppButton {
        x: root.width - config.button_width - config.button_border_width
        y: root.height - config.button_height
        image: "apply.png"
        onClicked: { var i=0
                     for (i=0;i<settingsArea.actions.length;i++) {
                         if (settingsArea.actions[i].checked != settingsArea.buttons[i].checked)
                             settingsArea.actions[i].trigger()
                     }
                     settingsArea.close()
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
