
import Qt 4.7

Item {
    id: aboutDialogArea
    signal close
    property variant items: ["","","",""]

    MouseArea {
        anchors.fill: parent
        onClicked: aboutDialogArea.close()
    }
    Rectangle {
        color: "#" + config.background
        anchors.fill: parent
        opacity: .9
    }
    Image {
        x: 10
        y: 10
        smooth: true
        source: "panucci_64x64.png"
    }
    Text {
        id: about_name
        x: 90
        y: 10
        font.pixelSize: config.font_size + 3
        font.weight: Font.Bold
        color: "#" + config.foreground
        text: items[0]
    }
    Text {
        id: about_text
        x: 90
        y: about_name.y + config.font_size + 13
        font.pixelSize: config.font_size + 1
        color: "#" + config.foreground
        text: items[1]
    }
    Text {
        id: about_copyright
        x: 90
        y: about_text.y + config.font_size + 11
        font.pixelSize: config.font_size + 1
        color: "#" + config.foreground
        text: items[2]
    }
    Text {
        id: about_website
        x: 90
        y: about_copyright.y + config.font_size + 11
        font.pixelSize: config.font_size + 1
        color: "#" + config.highlight
        text: "<a href=\"" + items[3] + "\">" + items[3] + "</a>"
        onLinkActivated: main.open_external_url(link)
    }
    /*
    Rectangle {
        x: 90
        y: about_website.y + config.font_size + 15
        color: "#" + config.button_color
        width: config.button_width
        height: config.button_height
        border.color: "#" + config.button_border_color
        border.width: config.button_border_width
        radius: 10
        smooth: true

        Image {
        anchors.centerIn: parent
        smooth: true
        source: "close.png"
        }
        MouseArea {
            anchors.fill: parent
            onClicked: {aboutDialogArea.close()}
        }
    }
    */
}
