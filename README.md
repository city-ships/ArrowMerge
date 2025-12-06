# ArrowMerge

A clean, Python-based visual Diff & Merge tool built with PyQt6. Designed with user-friendly terminology and TDD principles.

## Features

- **Visual Diffing**: Clear, highlighted differences between files.
- **Intra-line Diffs**: Highlights specific word changes within lines, not just whole lines.
- **Easy Merging**: 
  - **Word-Level Merging**: Copy specific word changes with a single click.
  - **Line-Level Merging**: Copy entire lines.
- **User-Friendly Terminology**: Uses "Previous" / "Changed" and "Copy/Revert" instead of confusing "Push/Pull" git jargon.
- **Visual Direction**: Clear arrow indicators (**⮕**, **⬅**) showing exactly where changes will move.
- **Sync Scrolling**: Both panes scroll together for easy comparison.

## Tech Stack

- **Language**: Python 3
- **GUI**: PyQt6
- **Architecture**: Strict MVC (Model-View-Controller) pattern.
- **Testing**: Built using Test-Driven Development (TDD) for core logic.

## Installation

1. Clone functionality repository:
   ```bash
   git clone https://github.com/yourusername/arrowmerge.git
   cd arrowmerge
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main application:

```bash
python -m arrowmerge.main
```

## Running Tests

To verify the logic, runs the unit tests:

```bash
python test_diff_logic.py   # Test the core Diff Model
python test_view_logic.py   # Test the UI Label logic
```

## License

MIT
