
import Qt 4.7

Item {
    id: filechooserArea
    signal close
    property variant items: []
    property variant path: ""
    property variant action: ""

    MouseArea {
        anchors.fill: parent
    }
    Rectangle {
        color: "#" + config.background
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
        
        highlight: Rectangle { color: "#" + config.highlight
                               width: filechooserView.width
                               height: config.font_size * 3
                               y: filechooserView.currentItem?filechooserView.currentItem.y:root.height
                   }
        highlightFollowsCurrentItem: false
        
        delegate: FilechooserItem {
            property variant item: modelData
            Image {
                x: 10
                source: modelData.directory ? "folder.png" : "file.png"
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
                color: "#" + config.foreground
                font.pixelSize: config.font_size
                text: modelData.caption
            }
            onSelected: {
                filechooserView.currentIndex = index
                filechooserArea.path = modelData.path + "/" + modelData.caption
                if (modelData.directory == true) {
                    filechooserView.currentIndex = -1
                    main.filechooser_callback("open", filechooserArea.path)
                    
                }
            }
        }
    }
    Rectangle {
        width: root.width
        height: config.font_size * 1.1
        x: 0
        y: root.height - config.button_height - textinput.height - config.button_border_width
        color: "#" + config.progress_bg_color
    }
    TextInput {
        id: textinput
        width: root.width
        x: 5
        y: root.height - config.button_height - textinput.height - config.button_border_width
        color: "#" + config.foreground
        font.pixelSize: config.font_size
        text: filechooserArea.path
    }
    Rectangle {
        x: 0
        y: root.height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            anchors.centerIn: parent
            smooth: true
            source: "home.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { filechooserView.currentIndex = -1
                         main.filechooser_callback("open", "~")
                       }
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2)
        y: root.height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            anchors.centerIn: parent
            smooth: true
            source: "left.png"
        }
        MouseArea {
            anchors.fill: parent
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 2
        y: root.height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            anchors.centerIn: parent
            smooth: true
            source: "right.png"
        }
        MouseArea {
            anchors.fill: parent
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 3
        y: root.height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            anchors.centerIn: parent
            smooth: true
            source: "up.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { filechooserView.currentIndex = -1
                         if (filechooserView.currentItem)
                             main.filechooser_callback("up", filechooserView.currentItem.item.path)
                         else
                             main.filechooser_callback("up", filechooserArea.path)
                       }
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 4
        y: root.height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            anchors.centerIn: parent
            smooth: true
            source: "cancel.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { filechooserView.currentIndex = -1
                         filechooserArea.close()
                       }
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 5
        y: root.height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
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
            onClicked: { filechooserArea.close()
                         filechooserView.currentIndex = -1
                         main.filechooser_callback(filechooserArea.action, textinput.text)
                       }
        }
    }
}
