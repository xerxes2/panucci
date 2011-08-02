import Qt 4.7
import com.nokia.meego 1.0

PageStackWindow {
    id: rootWindow
    property variant root: mainObject
    width: config.main_width
    height: config.main_height

    initialPage: Page {
        id: mainPage
        orientationLock: PageOrientation.LockLandscape

        Main {
            id: mainObject
            anchors.fill: parent
        }
    }
}
