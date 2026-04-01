---
name: desktop-automation
description: "Control desktop - click, type, move windows using pyautogui. Use when user needs to interact with GUI apps, accept RustDesk prompts, click buttons, or automate desktop tasks."
---

# Desktop Automation Skill

Control mouse, keyboard, and windows on the desktop.

## Setup

Requires: `pip3 install pyautogui`

## Tools

- **pyautogui** - Python library for mouse/keyboard automation
- **xdotool** - Linux window automation (if installed)

## Commands

### Click
```python
import pyautogui
pyautogui.click(x, y)  # Click at coordinates
pyautogui.click()  # Click at current position
```

### Type
```python
pyautogui.typewrite("Hello world")
pyautogui.press("enter")
```

### Move Mouse
```python
pyautogui.moveTo(x, y)
pyautogui.dragTo(x, y)  # Click and drag
```

### Windows
```python
# Get window by title
windows = pyautogui.getWindowsWithTitle("RustDesk")
window.activate()
window.maximize()
window.close()
```

## RustDesk Usage

Accept incoming connection:
```python
import pyautogui
# Click Accept button - find position first
pyautogui.click(x=500, y=400)  # Adjust coordinates as needed
```

## Note

Run `sudo apt-get install xdotool wmctrl` for more robust Linux window control.