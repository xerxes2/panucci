
import Qt 4.7

Rectangle {
    property variant image: ""
    signal clicked
    signal pressed
    signal released
    id: appButton
    width: config.button_width
    height: config.button_height
    color: "#" + config.button_color
    border.width: config.button_border_width
    border.color: "#" + config.button_border_color
    radius: config.button_radius
    smooth: true
    
    Image {
        anchors.centerIn: parent
        source: appButton.image
        smooth: true
    }
    MouseArea {
        anchors.fill: parent
        onClicked: appButton.clicked()
        onPressed: appButton.pressed()
        onReleased: appButton.released()        
    }
}
