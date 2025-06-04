// MIT License
// Copyright (c) 2025 Mark Pors

import QtQuick 6.5
import QtQuick.Window 6.5
import QtQuick.Effects
import QtMultimedia

Window {
    id: root
    property var settings
    width: 800;  height: 600
    visible: true
    title: "Image Classifier"
    visibility: Window.Maximized

    // Sound effect for successful classification
    SoundEffect {
        id: classifySound
        source: "yay.wav"
        volume: 0.7
    }

    Rectangle {
        id: content
        anchors.fill: parent
        focus: true
        Keys.priority: Keys.BeforeItem 
        Component.onCompleted: forceActiveFocus()

        // Cyberpunk gradient background
        gradient: Gradient {
            GradientStop { position: 0.0; color: "#0a0a0f" }
            GradientStop { position: 0.5; color: "#1a1a2e" }
            GradientStop { position: 1.0; color: "#0f0f1e" }
        }

        property string pendingLabel: ""
        property bool commitAllowed: false

        Timer {
            id: holdTimer
            interval: 1000
            repeat: false
            onTriggered: {
                content.commitAllowed = false;
                content.pendingLabel  = "";
                leftLabel.glowing = false;
                middleLabel.glowing = false;
                rightLabel.glowing = false;
            }
        }

        Keys.onPressed: (event) => {
            if (event.isAutoRepeat) return;

            if (event.key === Qt.Key_Down) {
                imageQueue.undo();
                return;
            }

            commitAllowed = true;
            holdTimer.restart();

            // Reset all glows
            leftLabel.glowing = false;
            middleLabel.glowing = false;
            rightLabel.glowing = false;

            switch (event.key) {
            case Qt.Key_Left:
                pendingLabel = "a";
                leftLabel.glowing = true;
                break;
            case Qt.Key_Up:
                pendingLabel = "unknown";
                middleLabel.glowing = true;
                break;
            case Qt.Key_Right:
                pendingLabel = "b";
                rightLabel.glowing = true;
                break;
            }
        }

        Keys.onReleased: (event) => {
            if (event.isAutoRepeat) return;

            holdTimer.stop();

            if (commitAllowed && pendingLabel !== "") {
                imageQueue.classify(pendingLabel);
                classifySound.play();
            }

            pendingLabel  = "";
            leftLabel.glowing = false;
            middleLabel.glowing = false;
            rightLabel.glowing = false;

            if (event.key === Qt.Key_Escape || event.key === Qt.Key_Q)
                Qt.quit();
        }

        /* ─── Neon Label Component ─────────────────────────────────── */
        component NeonLabel: Rectangle {
            property alias labelText: labelName.text
            property alias countText: labelCount.text
            property bool glowing: false
            property color neonColor: "#00ffff"
            property color glowColor: "#00ffff"

            width: 280; height: 120; radius: 16  // Much bigger!
            color: "#1a1a2e"
            border.width: 3
            border.color: glowing ? glowColor : Qt.rgba(glowColor.r, glowColor.g, glowColor.b, 0.3)

            // Animated glow intensity
            Behavior on border.color {
                ColorAnimation { duration: 200 }
            }

            // Outer glow effect - more pronounced
            Rectangle {
                anchors.centerIn: parent
                width: parent.width + 30
                height: parent.height + 30
                radius: parent.radius + 8
                color: "transparent"
                border.width: glowing ? 6 : 2
                border.color: glowing ? Qt.rgba(glowColor.r, glowColor.g, glowColor.b, 0.7) 
                                     : Qt.rgba(glowColor.r, glowColor.g, glowColor.b, 0.15)
                opacity: glowing ? 1.0 : 0.4
                z: -1

                Behavior on opacity {
                    NumberAnimation { duration: 200 }
                }
                Behavior on border.width {
                    NumberAnimation { duration: 200 }
                }
            }

            // Inner glow layer
            Rectangle {
                anchors.centerIn: parent
                width: parent.width - 10
                height: parent.height - 10
                radius: parent.radius - 4
                color: "transparent"
                opacity: glowing ? 0.6 : 0
                z: -1
                
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "transparent" }
                    GradientStop { position: 0.5; color: glowing ? Qt.rgba(glowColor.r, glowColor.g, glowColor.b, 0.3) : "transparent" }
                    GradientStop { position: 1.0; color: "transparent" }
                }
                
                Behavior on opacity {
                    NumberAnimation { duration: 200 }
                }
            }

            // Inner gradient
            gradient: Gradient {
                GradientStop { 
                    position: 0.0; 
                    color: glowing ? Qt.rgba(neonColor.r, neonColor.g, neonColor.b, 0.3) 
                                  : "#1a1a2e" 
                }
                GradientStop { 
                    position: 1.0; 
                    color: glowing ? Qt.rgba(neonColor.r, neonColor.g, neonColor.b, 0.15) 
                                  : "#16162a" 
                }
            }

            Column {
                anchors.centerIn: parent
                spacing: 8
                Text { 
                    id: labelName
                    color: parent.parent.glowing ? parent.parent.neonColor : "#ffffff"
                    font.bold: true
                    font.pixelSize: 28  // Bigger text
                    font.family: Qt.platform.os === "osx" ? "Menlo" :
                                Qt.platform.os === "windows" ? "Consolas" :
                                "DejaVu Sans Mono"
                    anchors.horizontalCenter: parent.horizontalCenter
                    Behavior on color {
                        ColorAnimation { duration: 200 }
                    }
                }
                Text { 
                    id: labelCount
                    color: parent.parent.glowing ? parent.parent.neonColor : "#888888"
                    font.pixelSize: 20  // Bigger count
                    font.family: Qt.platform.os === "osx" ? "Menlo" :
                                Qt.platform.os === "windows" ? "Consolas" :
                                "DejaVu Sans Mono"
                    anchors.horizontalCenter: parent.horizontalCenter
                    Behavior on color {
                        ColorAnimation { duration: 200 }
                    }
                }
            }

            // More pronounced pulse animation when glowing
            SequentialAnimation on scale {
                running: glowing
                loops: Animation.Infinite
                NumberAnimation { to: 1.08; duration: 400; easing.type: Easing.InOutQuad }
                NumberAnimation { to: 1.0; duration: 400; easing.type: Easing.InOutQuad }
            }
        }

        /* ─── header labels ─────────────────────────────────────────── */
        Rectangle {
            id: header
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.topMargin: 40
            height: 120
            color: "transparent"
            z: 1

            // Left label - Cyan theme
            NeonLabel {
                id: leftLabel
                labelText: settings.labels.a
                countText: imageQueue.countA
                neonColor: "#00ffff"
                glowColor: "#00ffff"
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 40
            }

            // Middle label - Magenta theme
            NeonLabel {
                id: middleLabel
                labelText: settings.labels.unknown
                countText: imageQueue.countUnknown
                neonColor: "#ff00ff"
                glowColor: "#ff00ff"
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
            }

            // Right label - Electric blue theme
            NeonLabel {
                id: rightLabel
                labelText: settings.labels.b
                countText: imageQueue.countB
                neonColor: "#0080ff"
                glowColor: "#0080ff"
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: 40
            }
        }

        /* ─── main picture with neon frame ──────────────────────────── */
        Rectangle {
            id: imageFrame
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: 40  // Push down a bit
            width: pic.width + 20
            height: pic.height + 20
            color: "transparent"
            border.width: 2
            border.color: "#333366"
            radius: 8
            visible: pic.visible

            // Subtle glow around image
            Rectangle {
                anchors.centerIn: parent
                width: parent.width + 10
                height: parent.height + 10
                color: "transparent"
                border.width: 1
                border.color: "#222244"
                radius: 12
                opacity: 0.5
                z: -1
            }
        }

        Image {
            id: pic
            source: imageQueue.currentImage
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: 40
            width: parent.width  * 0.5   // Reduced from 0.75
            height: parent.height * 0.5  // Reduced from 0.75
            fillMode: Image.PreserveAspectFit
            visible: source !== ""
            MouseArea { anchors.fill: parent; onClicked: imageQueue.next() }
        }

        /* ─── status line with neon styling ─────────────────────────── */
        Rectangle {
            id: statusContainer
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 20
            width: statusBar.width + 40
            height: 30
            color: "#1a1a2e"
            border.width: 1
            border.color: "#444466"
            radius: 15

            Text {
                id: statusBar
                text: "Controller: " + joyStatus.state + "  |  " + imageQueue.stats
                anchors.centerIn: parent
                color: "#00ffcc"
                font.family: Qt.platform.os === "osx" ? "Menlo" :
                             Qt.platform.os === "windows" ? "Consolas" :
                             "DejaVu Sans Mono"
                font.pixelSize: 12
            }

            // Animated gradient for status bar
            gradient: Gradient {
                GradientStop { position: 0.0; color: "#1a1a2e" }
                GradientStop { position: 0.5; color: "#222244" }
                GradientStop { position: 1.0; color: "#1a1a2e" }
            }
        }
    }
}