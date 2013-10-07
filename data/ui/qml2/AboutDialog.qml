
import QtQuick 2.0

Item {
    id: aboutDialogArea
    signal close
    property variant items: ["","","",""]

    MouseArea {
        anchors.fill: parent
        onClicked: aboutDialogArea.close()
    }
    Rectangle {
        color: themeController.background
        anchors.fill: parent
        opacity: .9
    }
    Image {
        x: 10
        y: 10
        smooth: true
        source: "artwork/panucci_64x64.png"
    }
    Text {
        id: about_name
        x: 90
        y: 10
        font.pixelSize: config.font_size * 1.3
        font.weight: Font.Bold
        color: themeController.foreground
        text: items[0]
    }
    Text {
        id: about_text
        x: 90
        y: about_name.y + (config.font_size * 1.3) + config.font_size
        font.pixelSize: config.font_size * 1.1
        color: themeController.foreground
        text: items[1]
    }
    Text {
        id: about_copyright
        x: 90
        y: about_text.y + (config.font_size * 1.1) + config.font_size
        font.pixelSize: config.font_size * 1.1
        color: themeController.foreground
        text: items[2]
    }
    Text {
        id: about_website
        x: 90
        y: about_copyright.y + (config.font_size * 1.1) + config.font_size
        font.pixelSize: config.font_size * 1.3
        font.weight: Font.Bold
        color: themeController.highlight
        text: "<a href=\"" + items[3] + "\">" + items[3] + "</a>"
        onLinkActivated: main.open_external_url(link)
    }
}
