import QtQuick 6.5
import QtQuick.Window 6.5

Window {
    id: root
    property var settings
    width: 800;  height: 600
    visible: true
    title: "Image Classifier"
    visibility: Window.Maximized

    Rectangle {
        id: content
        anchors.fill: parent
        color: "#202020"
        focus: true
        Keys.priority: Keys.BeforeItem 
        Component.onCompleted: forceActiveFocus()   // ensure focus at startup

        property string pendingLabel: ""
        property bool commitAllowed: false          // true while 1-s timer running

        Timer {
            id: holdTimer
            interval: 1000        // 1 second
            repeat: false
            onTriggered: {
                // Held too long → cancel
                content.commitAllowed = false;
                content.pendingLabel  = "";
                leftLabel.border.width =
                middleLabel.border.width =
                rightLabel.border.width = 0;
            }
        }

        Keys.onPressed: (event) => {
            if (event.isAutoRepeat) return;

            // --- UNDO with Down arrow ---
            if (event.key === Qt.Key_Down) {
                imageQueue.undo();
                return;
            }

            commitAllowed = true;      // assume we’ll commit unless timer expires
            holdTimer.restart();       // (re)start 1-second countdown

            // clear previous highlight
            leftLabel.border.width =
            middleLabel.border.width =
            rightLabel.border.width = 0;

            switch (event.key) {
            case Qt.Key_Left:
                pendingLabel = "a";
                leftLabel.border.color = "red";
                leftLabel.border.width = 4;
                break;
            case Qt.Key_Up:
                pendingLabel = "unknown";
                middleLabel.border.color = "red";
                middleLabel.border.width = 4;
                break;
            case Qt.Key_Right:
                pendingLabel = "b";
                rightLabel.border.color = "red";
                rightLabel.border.width = 4;
                break;
            }
        }

        Keys.onReleased: (event) => {
            if (event.isAutoRepeat) return;

            holdTimer.stop();      // stop the countdown

            if (commitAllowed && pendingLabel !== "") {
                // Released within 1 s → commit (move) for *all* labels
                imageQueue.classify(pendingLabel);   // 'unknown' included
            }

            // Clear state and highlight
            pendingLabel  = "";
            leftLabel.border.width =
            middleLabel.border.width =
            rightLabel.border.width = 0;

            // Optional quit keys
            if (event.key === Qt.Key_Escape || event.key === Qt.Key_Q)
                Qt.quit();
        }

        /* ─── header labels ─────────────────────────────────────────── */
        Rectangle {
            id: header
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: 10
            height: 60
            color: "transparent"
            z: 1                                  // always above the image

            // left label
            Rectangle {
                id: leftLabel
                width: 180; height: 60; radius: 8; color: "#404040"
                border.color: "transparent"
                border.width: 0
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 10
                Column {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: settings.labels.a; color: "white"; font.bold: true }
                    Text { text: imageQueue.countA; color: "lightgray"; font.pixelSize: 12 }
                }
            }

            // middle label (delete / unknown)
            Rectangle {
                id: middleLabel
                width: 180; height: 60; radius: 8; color: "#404040"
                border.color: "transparent"
                border.width: 0
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                Column {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: settings.labels.unknown; color: "white"; font.bold: true }
                    Text { text: imageQueue.countUnknown; color: "lightgray"; font.pixelSize: 12 }
                }
            }

            // right label
            Rectangle {
                id: rightLabel
                width: 180; height: 60; radius: 8; color: "#404040"
                border.color: "transparent"
                border.width: 0                
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right; anchors.rightMargin: 10
                Column {
                    anchors.centerIn: parent
                    spacing: 2
                    Text { text: settings.labels.b; color: "white"; font.bold: true }
                    Text { text: imageQueue.countB; color: "lightgray"; font.pixelSize: 12 }
                }
            }
        }

        /* ─── main picture ──────────────────────────────────────────── */
        Image {
            id: pic
            source: imageQueue.currentImage
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width  * 0.75
            height: parent.height * 0.75
            fillMode: Image.PreserveAspectFit
            visible: source !== ""
            MouseArea { anchors.fill: parent; onClicked: imageQueue.next() }
        }

        /* ─── status line ───────────────────────────────────────────── */
        Text {
            id: statusBar
            text: "Controller: " + joyStatus.state
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom; anchors.bottomMargin: 10
            color: "#dddddd"
            z: 1
        }
    }
}