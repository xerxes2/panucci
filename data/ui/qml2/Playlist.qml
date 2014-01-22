
import QtQuick 2.0

Item {
    id: playlistArea
    signal close
    property variant items: []

    MouseArea {
        anchors.fill: parent
    }
    Rectangle {
        color: themeController.background
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
        highlight: Rectangle { color: themeController.highlight
                               width: playlistView.width
                               height: config.font_size * 3
                               y: playlistView.currentItem? playlistView.currentItem.y:root.height
                   }
        highlightFollowsCurrentItem: false

        delegate: PlaylistItem {
            property variant item: modelData
            property variant rect: currentRect
            Rectangle {
                   id: currentRect
                   color: themeController.progress_bg_color
                   anchors.fill: parent
                   opacity: main.track_int == index && playlistView.currentIndex != index? 1.0: 0.0
            }
            Text {
                anchors {
                    left: parent.left
                    right: parent.right
                    verticalCenter: parent.verticalCenter
                    leftMargin: modelData.bookmark_id == ""? config.font_size: config.font_size * 2
                }
                color: themeController.foreground
                font.pixelSize: config.font_size
                text: modelData.caption
            }
            onSelected: {
                playlistView.currentIndex = index
            }
        }
    }
    AppButton {
        id: button_add
        x: 0
        anchors.bottom: playlistArea.bottom
        image: "artwork/add.png"
        onClicked: {action_add_media.trigger()}
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2)
        y: button_add.y
        image: "artwork/remove.png"
        onClicked: { if (playlistView.currentItem)
                main.remove_callback(playlistView.currentItem.item.item_id, playlistView.currentItem.item.bookmark_id)
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 2
        y: button_add.y
        image: "artwork/jump-to.png"
        onClicked: { if (playlistView.currentItem)
                main.jump_to_callback(playlistView.currentItem.item.item_id, playlistView.currentItem.item.bookmark_id)
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 3
        y: button_add.y
        image: "artwork/information.png"
        onClicked: { if (playlistView.currentItem)
                main.playlist_item_info_callback(playlistView.currentItem.item.item_id)
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 4
        y: button_add.y
        image: "artwork/clear.png"
        onClicked: { action_clear_playlist.trigger()
                     playlist.items = []
        }
    }
    AppButton {
        x: (config.button_width + config.button_border_width + 2) * 5
        y: button_add.y
        image: "artwork/close.png"
        onClicked: {playlistArea.close()}
    }
}
