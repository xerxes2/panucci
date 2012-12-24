
import QtQuick 1.1

Item {
    id: filechooserArea
    signal close
    property variant items: []
    property variant path: ""
    property variant back: ""
    property variant forward: ""
    property variant action: ""

    MouseArea { anchors.fill: parent
    }
    Rectangle {
        color: themeController.background
        anchors.fill: parent
        opacity: .9
    }
    ListView {
        id: filechooserView
        width: root.width
        height: root.height - config.button_height - config.button_border_width - config.font_size + 4
        model: filechooserArea.items
        clip: true
        currentIndex: -1
        header: Item { height: config.font_size }
        footer: Item { height: config.font_size }

        highlight: Rectangle { color: themeController.highlight
                               width: filechooserView.width
                               height: config.font_size * 3
                               y: filechooserView.currentItem?filechooserView.currentItem.y:root.height
                   }
        highlightFollowsCurrentItem: false

        delegate: FilechooserItem {
            property variant item: modelData
            Image {
                x: 10
                source: modelData.directory ? "artwork/folder.png" : "artwork/file.png"
                anchors {
                    verticalCenter: parent.verticalCenter
                }
            }
            Text {
                anchors {
                    left: parent.left
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    leftMargin: 40
                }
                color: themeController.foreground
                font.pixelSize: config.font_size
                text: modelData.caption
            }
            onSelected: {
                filechooserView.currentIndex = index
                filechooserArea.path = modelData.path + "/" + modelData.caption
                if (modelData.directory == true) {
                    filechooserView.currentIndex = -1
                    filechooserArea.back = modelData.path
                    main.filechooser_callback("open", filechooserArea.path)
                }
            }
        }
    }
    Rectangle {
        width: root.width
        height: config.font_size * 1.6
        x: 0
        anchors { bottom: button_home.top
                  bottomMargin: 3
        }
        color: themeController.progress_bg_color

        TextInput {
            id: textinput
            width: root.width
            x: config.font_size * .1
            y: config.font_size * .1
            color: themeController.foreground
            font.pixelSize: config.font_size
            text: filechooserArea.path

            Keys.onPressed: {
                if (event.key == Qt.Key_Return) {
                    textinput.focus = false
                }
            }
        }
    }
    AppButton {
        id: button_home
        x: 0
        anchors.bottom: filechooserArea.bottom
        image: "artwork/home.png"
        onClicked: { filechooserView.currentIndex = -1
                     main.filechooser_callback("open", "~")
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2)
        y: button_home.y
        image: "artwork/left.png"
        onClicked: { filechooserView.currentIndex = -1
                     if (filechooserArea.back != "" && filechooserArea.back != filechooserArea.path) {
                         filechooserArea.forward = filechooserArea.path
                         main.filechooser_callback("open", filechooserArea.back)
                     }
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 2
        y: button_home.y
        image: "artwork/right.png"
        onClicked: { filechooserView.currentIndex = -1
                     if (filechooserArea.forward != "" && filechooserArea.forward != filechooserArea.path) {
                         filechooserArea.back = filechooserArea.path
                         main.filechooser_callback("open", filechooserArea.forward)
                     }
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 3
        y: button_home.y
        image: "artwork/up.png"
        onClicked: { filechooserView.currentIndex = -1
                     filechooserArea.back = filechooserArea.path
                     if (filechooserView.currentItem)
                         main.filechooser_callback("up", filechooserView.currentItem.item.path)
                     else
                         main.filechooser_callback("up", filechooserArea.path)
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 4
        y: button_home.y
        image: "artwork/cancel.png"
        onClicked: { filechooserView.currentIndex = -1
                     filechooserArea.close()
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 5
        y: button_home.y
        image: "artwork/apply.png"
        onClicked: { filechooserArea.close()
                     filechooserView.currentIndex = -1
                     main.filechooser_callback(filechooserArea.action, textinput.text)
        }
    }
}
