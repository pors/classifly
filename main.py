import sys, signal, pathlib, itertools, toml
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, Signal, Slot, Property

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


class ImageQueueOOOOOOLD(QObject):
    currentImageChanged = Signal(str)
    countsChanged = Signal()  # NEW: notify QML when folder counts change

    def __init__(self, images, cfg, parent=None):
        super().__init__(parent)
        self._base_dir = pathlib.Path(cfg["paths"]["base_dir"])
        self._labels = cfg["labels"]  # {'a': 'A', 'unknown': 'delete', 'b': 'B'}
        self._images = images  # list[str]
        self._idx = 0

        # --- count how many files already exist in each label folder ---
        self._counts = {}
        for key, label in self._labels.items():
            folder = self._base_dir / label
            if folder.exists():
                self._counts[key] = len([p for p in folder.iterdir() if p.is_file()])
            else:
                self._counts[key] = 0

    # read-only property exposed to QML
    @Property(str, notify=currentImageChanged)
    def currentImage(self):
        return self._images[self._idx] if self._images else ""

    # ----- live counters for each folder -----
    @Property(str, notify=countsChanged)
    def countA(self):
        return str(self._counts.get("a", 0))

    @Property(str, notify=countsChanged)
    def countUnknown(self):
        return str(self._counts.get("unknown", 0))

    @Property(str, notify=countsChanged)
    def countB(self):
        return str(self._counts.get("b", 0))

    def _advance(self):
        if not self._images:
            return
        self._idx %= len(self._images)
        self.currentImageChanged.emit(self.currentImage)

    # slot the UI can call
    @Slot()
    def next(self):
        if not self._images:
            return
        self._idx = (self._idx + 1) % len(self._images)
        self._advance()

    @Slot(str)
    def classify(self, label_key):
        """Move current file to `base_dir/label` and advance."""
        if not self._images:
            return
        current_path = pathlib.Path(self.currentImage)
        label_name = self._labels.get(label_key, "unknown")
        dest_dir = self._base_dir / label_name
        dest_dir.mkdir(exist_ok=True)
        dest_path = dest_dir / current_path.name
        # Ensure unique filename
        counter = 1
        while dest_path.exists():
            dest_path = dest_dir / f"{current_path.stem}_{counter}{current_path.suffix}"
            counter += 1
        current_path.rename(dest_path)

        # update live counts and notify QML
        if label_key in self._counts:
            self._counts[label_key] += 1
            self.countsChanged.emit()

        # remove from queue
        self._images.pop(self._idx)
        if self._idx >= len(self._images):
            self._idx = 0
        self._advance()


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


def main():
    cfg = load_cfg()
    imgs = list(itertools.islice(image_iter(cfg["paths"]["base_dir"]), 1000))
    app = QGuiApplication(sys.argv)

    # ✔  Let Ctrl-C in the terminal close the window cleanly
    # TODO: Use a more robust signal handling mechanism if needed
    signal.signal(signal.SIGINT, lambda *args: app.quit())

    eng = QQmlApplicationEngine()
    queue = ImageQueue(imgs, cfg)
    eng.rootContext().setContextProperty("imageQueue", queue)
    eng.setInitialProperties({"settings": cfg})
    eng.load("Main.qml")
    if not eng.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
