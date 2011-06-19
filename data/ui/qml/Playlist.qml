
import Qt 4.7

Item {
    id: playlistArea
    signal close
    property variant items: []

    MouseArea {
        anchors.fill: parent
    }
    Rectangle {
        color: "#" + config.background
        anchors.fill: parent
        opacity: .9
    }
    ListView {
        id: playlistView
        width: root.width
        height: root.height - config.button_height - config.button_border_width
        model: playlistArea.items
        clip: true
        header: Item { height: config.font_size }
        footer: Item { height: config.font_size }
        
        highlight: Rectangle { color: "#" + config.highlight
                               width: playlistView.width
                               height: config.font_size * 3
                               y: playlistView.currentItem.y
                   }
        highlightFollowsCurrentItem: false
        
        delegate: PlaylistItem {
            property variant item: modelData
            Text {
                anchors {
                    left: parent.left
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    leftMargin: modelData.bookmark_id == "" ? config.font_size : config.font_size * 2
                }
                color: "#" + config.foreground
                font.pixelSize: config.font_size
                text: modelData.caption
            }
            onSelected: {
                playlistView.currentIndex = index
            }
        }
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
        source: "add.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {action_add_media.trigger()}
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
        source: "remove.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { if (playlistView.currentItem)
                main.remove_callback(playlistView.currentItem.item.item_id, playlistView.currentItem.item.bookmark_id)
            }
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
        source: "jump-to.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { if (playlistView.currentItem)
                main.jump_to_callback(playlistView.currentItem.item.item_id, playlistView.currentItem.item.bookmark_id)
            }
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
        source: "information.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {playlistArea.close()}
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
        source: "clear.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: { action_clear_playlist.trigger()
                         playlist.items = []
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
        source: "close.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {playlistArea.close()}
        }
    }
}
