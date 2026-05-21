# Smart Bot - Python Desktop Automation Tool

## 📌 Project Overview
Smart Bot is a custom-built, advanced desktop automation application developed using Python. It features a comprehensive graphical user interface (GUI) built with Tkinter, allowing users to effortlessly record, edit, and playback complex mouse and keyboard macros to optimize repetitive daily workflows.

## 🚀 Key Features (What it does & How it works)
* **Macro Recording & Playback:** Accurately captures mouse clicks, scrolls, and keyboard strokes, saving them in a structured JSON format for precise playback.
* **Timeline Editor:** A built-in visual editor that allows users to view recorded steps, edit delay times, delete specific actions, and even insert new actions mid-macro.
* **Pause & Resume Support:** Unlike basic recorders, this tool supports pausing and resuming during both the recording phase and the playback phase.
* **Smart Paste (Auto Type):** A dedicated feature to instantly paste pre-defined text strings (Supports English/Sinhala) during a recording sequence.
* **Visual Screen Capture:** Automatically captures a small screenshot of the clicked area during recording, displaying it in the Timeline Editor for easy identification of actions.
* **Custom Loop Execution:** Users can set a specific repeat count to loop the automated workflow multiple times.

## 🎯 Benefits & Use Cases
* Eliminates repetitive, manual data entry tasks.
* Saves time by automating multi-step desktop workflows.
* Highly customizable through the timeline editor without needing to re-record entire sequences.

## ⌨️ Shortcuts & Controls
* `Esc` : Stop Recording OR Stop Playback instantly.
* `F8` : Auto Paste Text (Opens a dialog to enter text to be typed).
* `F9` : Pause / Resume (Works seamlessly for both Recording and Playback).

## ⚙️ Installation & Setup

### Prerequisites
Make sure you have **Python 3.x** installed on your system. 

### Required Libraries
The application relies on several external Python libraries. You can install them using `pip`:

(Note: Built-in libraries used include tkinter, time, threading, json, os, ctypes, shutil, and math which require no additional installation).

```bash
pip install pyautogui pynput pillow pyperclip


