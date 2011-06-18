
import Qt 4.7

Rectangle {
    id: root
    color: "#" + config.background
    width: config.main_width
    height: config.main_height

    MouseArea {
        anchors.fill: parent
        onClicked: openContextMenu()
    }
    function openContextMenu() {
        contextMenu.state = 'opened'
        contextMenu.items = [action_add_media, action_playlist, action_settings,
            action_play_one, action_save_playlist, action_clear_playlist, action_delete_bookmarks,
            action_timer, action_about, action_quit]
    }
    function openAboutDialog(items) {
        aboutDialog.state = 'opened'
        aboutDialog.items = items
    }
    function openPlaylist(open, items) {
        if (open)
            playlist.state = 'opened'
        playlist.items = items
    }
    function openSettings() {
        settings.state = 'opened'
    }
    function openFilechooser(items, path, action) {
        filechooser.state = 'opened'
        filechooser.items = items
        filechooser.path = path
        if (action)
            filechooser.action = action
    }
    function openSleepTimer() {
        sleepTimer.state = 'opened'
    }
    function set_text_x() {
        if (cover.source == "") {
            artist.x = (config.main_width - artist.width) / 2
            album.x = (config.main_width - album.width) / 2
            title_rect.x = 5
            title_rect.width = config.main_width - 10
            title.x = (config.main_width - title.width) / 2
        }
        else {
            artist.x = config.cover_height + 5
            album.x = config.cover_height + 5
            title_rect.x = config.cover_height + 5
            title_rect.width = config.main_width - cover.width - 10
            title.x = 0
        }
    }
    function start_scrolling_timer(start) {
        if (start)
            timer_scrolling.start()
        else {
            timer_scrolling.stop()
            set_text_x()
        }
    }
    function scrolling_labels() {
        if (cover.source == "") {
            title.scrolling_width = config.main_width
            title.scrolling_margin = 5
        }
        else {
            title.scrolling_width = config.main_width - cover.width
            title.scrolling_margin = 5 + cover.width
        }
        if (title.width > title.scrolling_width) {
            if (title.direction) {
                title.x = title.x - 1
                if (title.width + 10 < title.scrolling_width - title.x)
                    title.direction = false
            }
            else {
                title.x = title.x + 1
                if (title.x > 5)
                    title.direction = true
            }
        }
    }
    Timer {
         id: timer_back
         interval: config.dual_delay
         running: false
         repeat: false
         onTriggered: image_back.source = "gtk-goto-first-ltr.png"
    }
    Timer {
         id: timer_forward
         interval: config.dual_delay
         running: false
         repeat: false
         onTriggered: image_forward.source = "gtk-goto-last-ltr.png"
    }
    Timer {
         id: timer_scrolling
         interval: 100
         running: false
         repeat: true
         onTriggered: scrolling_labels()
    }
    Image {
        id: cover
        x: 0
        y: 5
        width: config.cover_height
        height: config.cover_height
        sourceSize.width: config.cover_height
        sourceSize.height: config.cover_height
        smooth: true
        source: main.cover_string

        MouseArea {
            anchors.fill: parent
            onClicked: {action_player_play.trigger()}
        }
    }
    Text {
        id: artist
        x: config.cover_height + 5
        y: config.cover_height / 4
        font.pixelSize: config.font_size + 1
        color: "#" + config.foreground
        text: main.artist_string
    }
    Text {
        id: album
        x: config.cover_height + 5
        y: (config.cover_height / 4) + config.font_size + 21
        font.pixelSize: config.font_size - 1
        color: "#" + config.foreground
        text: main.album_string
    }
    Rectangle {
        id: title_rect
        width: config.main_width - 10
        height: config.font_size + 3
        x: config.cover_height + 5
        y: (config.cover_height / 4) + ((config.font_size*2)) + 42
        color: "#" + config.background
        clip: true
        Text {
            id: title
            font.pixelSize: config.font_size + 1
            font.weight: Font.Bold
            color: "#" + config.foreground
            text: main.title_string
            property bool direction
            direction: true
            property int scrolling_width
            property int scrolling_margin
        }
    }
    Rectangle {
        id: progressBar
        x: 0
        y: config.main_height - config.button_height - config.progress_height - config.button_border_width
        width: config.main_width
        height: config.progress_height
        color: "#" + config.progress_bg_color

        MouseArea {
            anchors.fill: parent
            onClicked: main.on_progress_clicked(mouseX / progressBar.width)
        }
        Rectangle {
            width: parent.width*main.progress
            color: "#" + config.progress_color
            clip: true
            anchors {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
            }
        }
    }
    Text {
        anchors.centerIn: progressBar
        color: "#" + config.foreground
        font.pixelSize: config.font_size
        text: main.time_string
        verticalAlignment: Text.AlignVCenter
    }
    Rectangle {
        x: 0
        y: config.main_height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            id: image_back
            anchors.centerIn: parent
            smooth: true
            source: "media-skip-backward.png"
        }
        MouseArea {
            anchors.fill: parent
            onReleased: image_back.source = "media-skip-backward.png"
            onPressed: timer_back.start()
            onClicked: { if (timer_back.running == true) {
                             timer_back.stop()
                             action_player_rrewind.trigger()
                         }
                         else
                             action_player_skip_back.trigger()
                             image_back.source = "media-skip-backward.png" }
        }
    }
    Rectangle {
        x: config.button_width + config.button_border_width + 2
        y: config.main_height - config.button_height
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
            source: "media-seek-backward.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: action_player_rewind.trigger()
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 2
        y: config.main_height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            id: player_play
            anchors.centerIn: parent
            smooth: true
            source: main.play_pause_icon_path
        }
        MouseArea {
            anchors.fill: parent
            onClicked: action_player_play.trigger()
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 3
        y: config.main_height - config.button_height
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
            source: "media-seek-forward.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: action_player_forward.trigger()
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 4
        y: config.main_height - config.button_height
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: config.button_radius
        smooth: true

        Image {
            id: image_forward
            anchors.centerIn: parent
            smooth: true
            source: "media-skip-forward.png"
        }
        MouseArea {
            anchors.fill: parent
            onReleased: image_forward.source = "media-skip-forward.png"
            onPressed: timer_forward.start()
            onClicked: { if (timer_forward.running == true) {
                             timer_forward.stop()
                             action_player_fforward.trigger()
                         }
                         else
                             action_player_skip_forward.trigger()
                             image_forward.source = "media-skip-forward.png" }
        }
    }
    Rectangle {
        x: (config.button_width + config.button_border_width + 2) * 5
        y: config.main_height - config.button_height
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
            source: "bookmark-new.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: main.bookmark_callback()
        }
    }
    ContextMenu {
        id: contextMenu
        width: parent.width
        opacity: 0

        anchors {
            top: parent.top
            bottom: parent.bottom
        }

        onClose: contextMenu.state = 'closed'
        //onResponse: controller.contextMenuResponse(index)

        state: 'closed'

        Behavior on opacity { NumberAnimation { duration: 300 } }

        states: [
            State {
                name: 'opened'
                PropertyChanges {
                    target: contextMenu
                    opacity: 1
                }
                AnchorChanges {
                    target: contextMenu
                    anchors.right: root.right
                }
            },
            State {
                name: 'closed'
                PropertyChanges {
                    target: contextMenu
                    opacity: 0
                }
                AnchorChanges {
                    target: contextMenu
                    anchors.right: root.left
                }
                StateChangeScript {
                    //script: controller.contextMenuClosed()
                }
            }
        ]

        transitions: Transition {
            AnchorAnimation { duration: 150 }
        }
    }
    AboutDialog {
        id: aboutDialog
        width: parent.width
        opacity: 0

        anchors {
            top: parent.top
            bottom: parent.bottom
        }
        onClose: aboutDialog.state = 'closed'
        state: 'closed'
        Behavior on opacity { NumberAnimation { duration: 300 } }

        states: [
            State {
                name: 'opened'
                PropertyChanges {
                    target: aboutDialog
                    opacity: 1
                }
                AnchorChanges {
                    target: aboutDialog
                    anchors.right: root.right
                }
            },
            State {
                name: 'closed'
                PropertyChanges {
                    target: aboutDialog
                    opacity: 0
                }
                AnchorChanges {
                    target: aboutDialog
                    anchors.right: root.left
                }
                StateChangeScript {
                    //script: controller.contextMenuClosed()
                }
            }
        ]
        transitions: Transition {
            AnchorAnimation { duration: 150 }
        }
    }
    Playlist {
        id: playlist
        width: parent.width
        opacity: 0

        anchors {
            top: parent.top
            bottom: parent.bottom
        }
        onClose: playlist.state = 'closed'
        state: 'closed'
        Behavior on opacity { NumberAnimation { duration: 300 } }

        states: [
            State {
                name: 'opened'
                PropertyChanges {
                    target: playlist
                    opacity: 1
                }
                AnchorChanges {
                    target: playlist
                    anchors.right: root.right
                }
            },
            State {
                name: 'closed'
                PropertyChanges {
                    target: playlist
                    opacity: 0
                }
                AnchorChanges {
                    target: playlist
                    anchors.right: root.left
                }
                StateChangeScript {
                    //script: controller.contextMenuClosed()
                }
            }
        ]
        transitions: Transition {
            AnchorAnimation { duration: 150 }
        }
    }
    Filechooser {
        id: filechooser
        width: parent.width
        opacity: 0

        anchors {
            top: parent.top
            bottom: parent.bottom
        }
        onClose: filechooser.state = 'closed'
        state: 'closed'
        Behavior on opacity { NumberAnimation { duration: 300 } }

        states: [
            State {
                name: 'opened'
                PropertyChanges {
                    target: filechooser
                    opacity: 1
                }
                AnchorChanges {
                    target: filechooser
                    anchors.right: root.right
                }
            },
            State {
                name: 'closed'
                PropertyChanges {
                    target: filechooser
                    opacity: 0
                }
                AnchorChanges {
                    target: filechooser
                    anchors.right: root.left
                }
                StateChangeScript {
                    //script: controller.contextMenuClosed()
                }
            }
        ]
        transitions: Transition {
            AnchorAnimation { duration: 150 }
        }
    }
    Settings {
        id: settings
        width: parent.width
        opacity: 0

        anchors {
            top: parent.top
            bottom: parent.bottom
        }
        onClose: settings.state = 'closed'
        state: 'closed'
        Behavior on opacity { NumberAnimation { duration: 300 } }

        states: [
            State {
                name: 'opened'
                PropertyChanges {
                    target: settings
                    opacity: 1
                }
                AnchorChanges {
                    target: settings
                    anchors.right: root.right
                }
            },
            State {
                name: 'closed'
                PropertyChanges {
                    target: settings
                    opacity: 0
                }
                AnchorChanges {
                    target: settings
                    anchors.right: root.left
                }
                StateChangeScript {
                    //script: controller.contextMenuClosed()
                }
            }
        ]
        transitions: Transition {
            AnchorAnimation { duration: 150 }
        }
    }
    SleepTimer {
        id: sleepTimer
        width: parent.width
        opacity: 0

        anchors {
            top: parent.top
            bottom: parent.bottom
        }
        onClose: sleepTimer.state = 'closed'
        state: 'closed'
        Behavior on opacity { NumberAnimation { duration: 300 } }

        states: [
            State {
                name: 'opened'
                PropertyChanges {
                    target: sleepTimer
                    opacity: 1
                }
                AnchorChanges {
                    target: sleepTimer
                    anchors.right: root.right
                }
            },
            State {
                name: 'closed'
                PropertyChanges {
                    target: sleepTimer
                    opacity: 0
                }
                AnchorChanges {
                    target: sleepTimer
                    anchors.right: root.left
                }
                StateChangeScript {
                    //script: controller.contextMenuClosed()
                }
            }
        ]
        transitions: Transition {
            AnchorAnimation { duration: 150 }
        }
    }
}
