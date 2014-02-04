
import QtQuick 2.0

Item {
    id: playlistItemInfoEditArea
    signal close
    property string item_id
    property string image: ""
    property bool modified: false
    property var metadata: {"artist":"","title":"","album":""}
    property var open: openArea
    onClose: { playlistItemInfoEditArea.focus = true
    }
    function openArea() { artist_input.focus = true
    }
    function save() {
        metadata["artist"] = artist_input.text
        metadata["title"] = title_input.text
        metadata["album"] = album_input.text
        main.playlist_item_info_edit_callback(item_id, metadata, image, modified)
    }
    MouseArea {
        anchors.fill: parent
        onClicked: playlistItemInfoEditArea.close()
    }
    Rectangle {
        color: themeController.background
        anchors.fill: parent
        opacity: .9
    }
    Column {
        id: leftColumn
        x: config.font_size
        y: config.font_size
        spacing: config.font_size / 4

        Item {
            width: info_artist_text.width
            height: config.font_size * 1.7
            anchors.right: parent.right
            Text {
                id: info_artist_text
                anchors { right: parent.right
                          verticalCenter: parent.verticalCenter
                }
                color: themeController.foreground
                font.pixelSize: config.font_size * 1.2
                text: info_artist_str
            }
        }
        Item {
            width: info_title_text.width
            height: config.font_size * 1.7
            anchors.right: parent.right
            Text {
                id: info_title_text
                anchors { right: parent.right
                          verticalCenter: parent.verticalCenter
                }
                color: themeController.foreground
                font.pixelSize: config.font_size * 1.2
                text: info_title_str
            }
        }
        Item {
            width: info_album_text.width
            height: config.font_size * 1.7
            anchors.right: parent.right
            Text {
                id: info_album_text
                anchors { right: parent.right
                          verticalCenter: parent.verticalCenter
                }
                color: themeController.foreground
                font.pixelSize: config.font_size * 1.2
                text: info_album_str
            }
        }
    }
    Item {
        width: leftColumn.width + config.font_size
        height: leftColumn.height + config.font_size
        x: 0
        y: 0
        MouseArea { 
            anchors.fill: parent
            onClicked: {
                artist_input.focus = false
                title_input.focus = false
                album_input.focus = false
            }
        }
    }
    Item {
        width: rightColumn.width
        height: rightColumn.height
        anchors {
            top: leftColumn.top
            left: leftColumn.right
        }
        MouseArea { anchors.fill: parent
        }
    }
    Column {
        id: rightColumn
        spacing: config.font_size / 4
        anchors {
            top: leftColumn.top
            left: leftColumn.right
            leftMargin: config.font_size / 2
        }
        
        Rectangle {
            width: root.width / 2
            height: config.font_size * 1.7
            color: themeController.progress_bg_color
            radius: config.font_size / 4
            
            TextInput {
                id: artist_input
                width: parent.width - config.font_size
                height: config.font_size * 1.3
                anchors.centerIn: parent
                color: themeController.foreground
                font.pixelSize: config.font_size
                clip: true
                text: playlistItemInfoEditArea.metadata["artist"]

                Keys.onPressed: { if (event.key == Qt.Key_Return) {
                                      title_input.focus = true
                                  }
                }
            }
        }
        Rectangle {
            width: root.width / 2
            height: config.font_size * 1.7
            color: themeController.progress_bg_color
            radius: config.font_size / 4
            
            TextInput {
                id: title_input
                width: parent.width - config.font_size
                height: config.font_size * 1.3
                anchors.centerIn: parent
                color: themeController.foreground
                font.pixelSize: config.font_size
                clip: true
                text: playlistItemInfoEditArea.metadata["title"]

                Keys.onPressed: { if (event.key == Qt.Key_Return) {
                                      album_input.focus = true
                                  }
                }
            }
        }
        Rectangle {
            width: root.width / 2
            height: config.font_size * 1.7
            color: themeController.progress_bg_color
            radius: config.font_size / 4
            
            TextInput {
                id: album_input
                width: parent.width - config.font_size
                height: config.font_size * 1.3
                anchors.centerIn: parent
                color: themeController.foreground
                font.pixelSize: config.font_size
                clip: true
                text: playlistItemInfoEditArea.metadata["album"]

                Keys.onPressed: { if (event.key == Qt.Key_Return) {
                                      album_input.focus = false
                                  }
                }
            }
        }
    }
    Image {
        width: root.width - leftColumn.width - rightColumn.width - (config.font_size * 4)
        height: width
        source: playlistItemInfoEditArea.image
        anchors {
            top: rightColumn.top
            left: rightColumn.right
            leftMargin: config.font_size / 2
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {
                main.add_coverart_callback()
                playlistItemInfoEditArea.focus = true
            }
        }
    }
    AppButton {
        anchors { right: playlistItemInfoEditArea.right
                  bottom: playlistItemInfoEditArea.bottom
        }
        image: "artwork/apply.png"
        onClicked: { playlistItemInfoEditArea.save()
                     playlistItemInfoEditArea.close()
        }
    }
}
