import pygame
import sys, signal, pathlib, itertools, toml
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QEvent, Qt
from PySide6.QtGui import QKeyEvent

CFG = pathlib.Path("settings.toml")
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


class ImageQueue(QObject):
    # ----- signals ----------------------------------------------------
    currentImageChanged = Signal(str)  # image → QML
    countsChanged = Signal()  # counters → QML

    # ------------------------------------------------------------------
    def __init__(self, images, cfg, parent=None):
        super().__init__(parent)

        # config
        self._base_dir = pathlib.Path(cfg["paths"]["base_dir"])
        self._labels = cfg["labels"]  # {"a":"LAMP", "unknown":"skip", "b":"NO LAMP"}

        # queue state
        self._images = images  # list[str]
        self._idx = 0

        # counters for header UI
        self._counts = {}
        for key, label in self._labels.items():
            folder = self._base_dir / label
            self._counts[key] = (
                len([p for p in folder.iterdir() if p.is_file()])
                if folder.exists()
                else 0
            )

        # history stack for one-level undo
        # each entry: (label_key, dest_path, original_path)
        self._history = []

    # ----- properties -------------------------------------------------
    @Property(str, notify=currentImageChanged)
    def currentImage(self):
        return self._images[self._idx] if self._images else ""

    @Property(str, notify=countsChanged)
    def countA(self):
        return str(self._counts.get("a", 0))

    @Property(str, notify=countsChanged)
    def countUnknown(self):
        return str(self._counts.get("unknown", 0))

    @Property(str, notify=countsChanged)
    def countB(self):
        return str(self._counts.get("b", 0))

    # ----- public slots ----------------------------------------------
    @Slot()
    def next(self):
        if not self._images:
            return
        self._idx = (self._idx + 1) % len(self._images)
        self.currentImageChanged.emit(self.currentImage)

    @Slot(str)
    def classify(self, label_key):
        """Move current image into its label folder and advance."""
        if not self._images:
            return

        current_path = pathlib.Path(self.currentImage)
        label_name = self._labels.get(label_key, "unknown")
        dest_dir = self._base_dir / label_name
        dest_dir.mkdir(exist_ok=True)

        # ensure unique filename
        dest_path = dest_dir / current_path.name
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{current_path.stem}_{counter}{current_path.suffix}"
            counter += 1

        current_path.rename(dest_path)

        # remember for undo
        self._history.append((label_key, str(dest_path), str(current_path)))

        # update counters
        self._counts[label_key] = self._counts.get(label_key, 0) + 1
        self.countsChanged.emit()

        # remove from queue and advance
        self._images.pop(self._idx)
        if self._idx >= len(self._images):
            self._idx = 0
        self.currentImageChanged.emit(self.currentImage)

    @Slot()
    def undo(self):
        """Undo last classify (single level)."""
        if not self._history:
            return

        label_key, moved_str, original_str = self._history.pop()
        moved_path = pathlib.Path(moved_str)
        original_path = pathlib.Path(original_str)

        if moved_path.exists():
            moved_path.rename(original_path)

        # decrement counter and notify
        if self._counts.get(label_key, 0) > 0:
            self._counts[label_key] -= 1
            self.countsChanged.emit()

        # re-insert image at current position and refresh display
        self._images.insert(self._idx, str(original_path))
        self.currentImageChanged.emit(self.currentImage)


def image_iter(base):
    root = pathlib.Path(base or ".")
    for p in root.rglob("*"):
        if p.suffix.lower() in IMG_EXT:
            yield str(p)


def load_cfg():
    if not CFG.exists():  # write a minimal template on first run
        CFG.write_text(
            "[paths]\nbase_dir = ''\n"
            "[labels]\na = 'A'\nunknown = 'delete'\nb = 'B'\n"
            "[controller]\nleft = 4  # LB\nright = 5  # RB\nmiddle = 0  # A\n"
        )
    return toml.loads(CFG.read_text())


# ---------------- JoystickBridge -----------------
class JoystickBridge(QObject):
    stateChanged = Signal()                     # notify QML when state text changes

    @Property(str, notify=stateChanged)
    def state(self):
        return self._state

    def __init__(self, window, cfg, parent=None):
        super().__init__(parent)
        self._state = "disconnected"
        self._window = window  # the QML Window that owns the Keys handler
        self._map = cfg["controller"]  # {'left':4, 'right':5, 'middle':0, 'undo':1}
        pygame.init()
        pygame.joystick.init()
        self._joy = None
        self._timer = QTimer(self, timeout=self._poll)
        self._timer.start(16)  # ~60 Hz

    def attach_window(self, window):
        """Provide the QML root window after it’s created."""
        self._window = window

    def _send(self, qt_key, pressed):
        if self._window is None:
            return
        typ = QEvent.Type.KeyPress if pressed else QEvent.Type.KeyRelease
        ev = QKeyEvent(typ, qt_key, Qt.NoModifier)
        QGuiApplication.postEvent(self._window, ev)

    def _ensure_joystick(self):
        if not self._joy and pygame.joystick.get_count():
            self._joy = pygame.joystick.Joystick(0)
            self._joy.init()
            self._state = "connected"
            self.stateChanged.emit()
        elif self._joy and not pygame.joystick.get_count():
            self._joy = None
            self._state = "disconnected"
            self.stateChanged.emit()

    def _poll(self):
        self._ensure_joystick()
        if not self._joy:
            return
        for evt in pygame.event.get():
            if evt.type in (pygame.JOYBUTTONDOWN, pygame.JOYBUTTONUP):
                pressed = evt.type == pygame.JOYBUTTONDOWN
                if evt.button == self._map["left"]:
                    self._send(Qt.Key_Left, pressed)
                elif evt.button == self._map["right"]:
                    self._send(Qt.Key_Right, pressed)
                elif evt.button == self._map["middle"]:
                    self._send(Qt.Key_Up, pressed)
                elif evt.button == self._map.get("undo", -1):
                    self._send(Qt.Key_Down, pressed)


def main():
    cfg = load_cfg()
    imgs = list(itertools.islice(image_iter(cfg["paths"]["base_dir"]), 1000))
    app = QGuiApplication(sys.argv)

    # ✔  Let Ctrl-C in the terminal close the window cleanly
    # TODO: Use a more robust signal handling mechanism if needed
    signal.signal(signal.SIGINT, lambda *args: app.quit())

    eng = QQmlApplicationEngine()

    # --- create queue & joystick bridge BEFORE loading QML ---
    queue   = ImageQueue(imgs, cfg)
    jbridge = JoystickBridge(None, cfg)      # no window yet

    ctx = eng.rootContext()
    ctx.setContextProperty("imageQueue", queue)
    ctx.setContextProperty("joyStatus",  jbridge)
    eng.setInitialProperties({"settings": cfg})

    eng.load("Main.qml")
    if not eng.rootObjects():
        sys.exit(-1)

    root_win = eng.rootObjects()[0]
    jbridge.attach_window(root_win)          # now we have the window

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
