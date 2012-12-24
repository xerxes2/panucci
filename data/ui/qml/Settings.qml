
import QtQuick 1.1
import "themeGenerator.js" as Generator

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
        id: settingsFlick
        width: rootWindow.width - config.button_width - config.button_border_width
        height: rootWindow.height
        contentWidth: width
        contentHeight: height
        clip: true

        MouseArea {
            anchors.fill: parent
            onClicked: settingsArea.close()
        }
        Text {
            id: main_window_text
            y: config.font_size
            anchors.horizontalCenter: parent.horizontalCenter
            text: main_window_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
        SettingsButton {
            id: action_scrolling_labels_button
            checked: action_scrolling_labels.checked
            y: main_window_text.y + (config.font_size * 2.5)
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
            y: action_scrolling_labels_button.y + (config.font_size * 5)
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
            y: action_lock_progress_button.y + (config.font_size * 5)
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
            id: playback_text
            y: action_dual_action_button.y + (config.font_size * 5.5)
            anchors.horizontalCenter: parent.horizontalCenter
            text: playback_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
        SettingsButton {
            id: action_stay_at_end_button
            checked: action_stay_at_end.checked
            y: playback_text.y + (config.font_size * 2.5)
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
            y: action_stay_at_end_button.y + (config.font_size * 5.5)
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
            y: action_seek_back_button.y + (config.font_size * 5.5)
            text: action_resume_all.text
            onClicked: { if (action_resume_all_button.checked) {
                             action_resume_all_button.checked = false
                         }
                         else {
                             action_resume_all_button.checked = true
                         }
            }
        }
        SettingsButton {
            id: action_play_on_headset_button
            checked: action_play_on_headset.checked
            y: action_resume_all_button.y + (config.font_size * 5.5)
            text: action_play_on_headset.text
            onClicked: { if (action_play_on_headset_button.checked) {
                             action_play_on_headset_button.checked = false
                         }
                         else {
                             action_play_on_headset_button.checked = true
                         }
            }
        }
        Text {
            id: play_mode_text
            y: action_play_on_headset_button.y + (config.font_size * 5.5)
            anchors.horizontalCenter: parent.horizontalCenter
            text: play_mode_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
        SettingsButtonSmall {
            id: action_play_mode_all_button
            checked: action_play_mode_all.checked
            x: parent.width / 25
            y: play_mode_text.y + (config.font_size * 2.5)
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
            x: (parent.width / 25 * 2) + width
            y: action_play_mode_all_button.y
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
            x: (parent.width / 25 * 3) + (width * 2)
            y: action_play_mode_all_button.y
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
            x: (parent.width / 25 * 4) + (width * 3)
            y: action_play_mode_all_button.y
            text: action_play_mode_repeat.text
            onClicked: { action_play_mode_all_button.checked = false
                         action_play_mode_single_button.checked = false
                         action_play_mode_random_button.checked = false
                         action_play_mode_repeat_button.checked = true
            }
        }
        Text {
            id: headset_button_text
            y: action_play_mode_all_button.y + (config.font_size * 5.5)
            anchors.horizontalCenter: parent.horizontalCenter
            text: headset_button_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
        SettingsButtonSmall {
            id: action_headset_button_short_button
            checked: action_headset_button_short.checked
            x: ((parent.width / 5 * 2) - (parent.width / 25 * 2)) / 2
            y: headset_button_text.y + (config.font_size * 2.5)
            text: action_headset_button_short.text
            onClicked: { action_headset_button_short_button.checked = true
                         action_headset_button_long_button.checked = false
                         action_headset_button_switch_button.checked = false
           }
        }
        SettingsButtonSmall {
            id: action_headset_button_long_button
            checked: action_headset_button_long.checked
            x: action_headset_button_short_button.x + width + (parent.width / 25)
            y: action_headset_button_short_button.y
            text: action_headset_button_long.text
            onClicked: { action_headset_button_short_button.checked = false
                         action_headset_button_long_button.checked = true
                         action_headset_button_switch_button.checked = false
           }
        }
        SettingsButtonSmall {
            id: action_headset_button_switch_button
            checked: action_headset_button_switch.checked
            x: action_headset_button_long_button.x + width + (parent.width / 25)
            y: action_headset_button_short_button.y
            text: action_headset_button_switch.text
            onClicked: { action_headset_button_short_button.checked = false
                         action_headset_button_long_button.checked = false
                         action_headset_button_switch_button.checked = true
           }
        }
        Text {
            id: theme_text
            y: action_headset_button_short_button.y + (config.font_size * 5.5)
            anchors.horizontalCenter: parent.horizontalCenter
            text: theme_str
            font.pixelSize: config.font_size * 1.5
            color: themeController.foreground
        }
    }
    AppButton {
        anchors { right: settingsArea.right
                  bottom: settingsArea.bottom
        }
        image: "artwork/apply.png"
        onClicked: { var i=0
                     for (i=0;i<settingsArea.actions.length;i++) {
                         if (settingsArea.actions[i].checked != settingsArea.buttons[i].checked)
                             settingsArea.actions[i].trigger()
                     }
                     settingsArea.close()
                   }
    }
    Component.onCompleted: Generator.createThemeButtons()
    function themeButtonClicked(button) {
        var i
        for (i=0;i<themes.length;i++) {
            Generator.themeButtons[i].checked = false
        }
        button.checked = true
        themeController.set_theme(button.text)
    }
    property variant actions: [action_scrolling_labels, action_lock_progress,
            action_dual_action, action_stay_at_end, action_seek_back,
            action_resume_all, action_play_on_headset,
            action_play_mode_all, action_play_mode_single,
            action_play_mode_random, action_play_mode_repeat,
            action_headset_button_short, action_headset_button_long, action_headset_button_switch]
    property variant buttons: [action_scrolling_labels_button, action_lock_progress_button,
            action_dual_action_button, action_stay_at_end_button, action_seek_back_button,
            action_resume_all_button, action_play_on_headset_button,
            action_play_mode_all_button, action_play_mode_single_button,
            action_play_mode_random_button, action_play_mode_repeat_button,
            action_headset_button_short_button, action_headset_button_long_button, action_headset_button_switch_button]
    onClose: { var i=0
               for (i=0;i<settingsArea.actions.length;i++) {
                   settingsArea.buttons[i].checked = settingsArea.actions[i].checked
               }
             }
}
