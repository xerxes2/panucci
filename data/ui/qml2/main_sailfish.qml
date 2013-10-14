
import QtQuick 2.0
import Sailfish.Silica 1.0

ApplicationWindow {
    id: rootWindow
    property variant root: mainObject
    //width: config.main_width
    //height: config.main_height
    cover: root.root

    initialPage: Page {
            id: mainPage
            allowedOrientations: Orientation.Landscape

            Main {
                id: mainObject
                anchors.fill: parent
            }
    }
    
}
