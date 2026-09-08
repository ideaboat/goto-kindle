# gotokindle     [中文版Readme](README_zh.md) 

One-click tool to send clipboard content (text/images) to your Kindle via USB (powered by Calibre).

## Features
- Automatically detects text or images from clipboard
- Short text (≤500 chars) → copied as TXT; long text → converted to MOBI with 16pt font
- Images generate a MOBI with inline image
- Auto-generates unique filenames (timestamp + random suffix)
- Checks if Kindle is mounted; prompts you to connect if not

## Dependencies
- Python 3.6+
- `pyperclip`, `Pillow`
- Calibre (with `ebook-convert` available in PATH)

## Installation
1. Clone this repo
2. Install dependencies: `pip3 install pyperclip Pillow`
3. Make sure Calibre is installed and `ebook-convert` is accessible (default macOS path: `/Applications/calibre.app/Contents/MacOS/ebook-convert`)

## Usage
```bash
gotokindle
```
(Recommend setting an alias or symlink to PATH)

License
MIT
