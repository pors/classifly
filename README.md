# classifly

Speed up image classification labelling with a game controller! 🎮

Classifly is a fast, gamified image labeling tool designed for binary classification tasks. Navigate through your image dataset using a game controller or keyboard, making the tedious task of labeling images feel more like playing a game.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![PySide6](https://img.shields.io/badge/PySide6-6.9.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

- **Game Controller Support**: Use Xbox, PlayStation, or GameSir controllers for rapid classification
- **Cyberpunk UI**: Neon-themed interface with glowing effects and visual feedback
- **Three-way Classification**: Sort images into two categories plus a "skip/unknown" option
- **Real-time Stats**: Track your progress with live counters, elapsed time, and ETA
- **Undo Support**: Made a mistake? Just press the undo button
- **Keyboard Fallback**: No controller? Use arrow keys
- **Batch Processing**: Handle up to 1000 images per session

## Requirements

- Python 3.8+
- PySide6
- pygame (for controller support)
- toml (for configuration)
- Optional: gamesir-t1d (for GameSir T1d Bluetooth controller)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/classifly.git
cd classifly
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Edit `settings.toml` to configure your setup:

```toml
[paths]
base_dir = '/path/to/your/images'  # Directory containing unclassified images

[labels]
a = 'Category_A'        # Left button - folder name for first category
unknown = 'skip'        # Up button - folder name for skipped images  
b = 'Category_B'        # Right button - folder name for second category

[controller]
# For GameSir T1d Bluetooth controller:
gamesir_t1d = 'Gamesir-T1d-XXXX'  # Your controller's Bluetooth name
left   = "l1"   # Left shoulder button
right  = "r1"   # Right shoulder button  
middle = "y"    # Y button for skip
undo   = "a"    # A button for undo

# For standard game controllers (Xbox/PlayStation):
# left = 4    # LB/L1
# right = 5   # RB/R1
# middle = 0  # A/X button
# undo = 1    # B/Circle button
```

## Usage

1. Place your unclassified images in the base directory specified in settings.toml
2. Run the application:

```bash
python main.py
```

3. Use your controller or keyboard to classify:

* **Left trigger/arrow**: Classify as Category A
* **Right trigger/arrow**: Classify as Category B
* **Up/Middle button**: Skip/Unknown
* **Down/Undo button**: Undo last classification

## Controls

### Controller

* Hold a classification button for <1 second to classify
* Hold for >1 second to cancel (prevents accidental classifications)
* The corresponding label will glow when pressed

### Keyboard

* Left Arrow: Category A
* Right Arrow: Category B
* Up Arrow: Skip/Unknown
* Down Arrow: Undo
* Escape/Q: Quit
* Click Image: Next image (without classifying)

## How It Works

1. Images are loaded from your base directory (excluding subdirectories)
2. When you classify an image, it's moved to the corresponding label folder
3. The app tracks your progress and shows real-time statistics
4. All moves are instant - no confirmation dialogs to slow you down
5. Undo moves the last classified image back to the queue

## Tips

* The app automatically creates label folders if they don't exist
* Only common image formats are supported: `.jpg`, `.jpeg`, `.png`, `.bmp`
* Images already in subfolders are not loaded (they're considered classified)
* The 1-second hold timer prevents accidental classifications
* Your progress is shown in real-time at the bottom of the screen

## File Structure

After classification, your directory will look like:

```
base_dir/
├── unclassified_image1.jpg
├── unclassified_image2.jpg
├── Category_A/
│   ├── classified_image1.jpg
│   └── classified_image2.jpg
├── Category_B/
│   ├── classified_image3.jpg
│   └── classified_image4.jpg
└── skip/
    └── skipped_image1.jpg
```

## Troubleshooting

* Controller not detected: Make sure pygame can see your controller. Test with `python -c "import pygame; pygame.init(); print(pygame.joystick.get_count())"`
* GameSir T1d: Ensure Bluetooth is enabled and the controller is paired. Update the device name in `settings.toml`
* Images not loading: Check that your images are directly in the base_dir, not in subdirectories

## Converting WebP Images

If you have WebP images, use the included converter script:

```bash
python convert_webp.py /path/to/images --recursive --remove
```

## License

MIT License - feel free to modify and use for your own classification tasks!