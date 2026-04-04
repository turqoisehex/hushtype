# hushtype

[![Release](https://img.shields.io/github/v/release/turqoisehex/hushtype)](https://github.com/turqoisehex/hushtype/releases/latest)
[![License](https://img.shields.io/github/license/turqoisehex/hushtype)](LICENSE)
[![Stars](https://img.shields.io/github/stars/turqoisehex/hushtype?style=social)](https://github.com/turqoisehex/hushtype)

**Real-time voice dictation for Windows** -- type anywhere with your voice using GPU-accelerated OpenAI Whisper speech-to-text.

hushtype is a system-wide voice typing tool that turns your microphone into a keyboard. Press **Ctrl+Alt+V** to start dictating into any application -- text editors, browsers, terminals, chat apps, IDEs, email. It runs silently in the background with a minimal status indicator and supports 40+ voice commands for editing, navigation, and formatting.

Unlike transcription tools that process pre-recorded audio files, hushtype is a **live input method** -- speech appears as typed text in real time, wherever your cursor is. All processing runs locally on your GPU. No audio data ever leaves your machine.

## Features

### Speech Recognition

- **OpenAI Whisper** speech-to-text engine (turbo model by default)
- **NVIDIA CUDA GPU acceleration** for fast, low-latency transcription
- **Silero VAD** (Voice Activity Detection) with ONNX optimization -- 4-5x faster than default
- **Streaming dictation** via RealtimeSTT with early transcription on silence
- **Configurable silence duration** -- control how long to wait before finalizing speech
- **Hallucination filtering** -- strips known Whisper ghost phrases (silence artifacts)
- **NVIDIA Broadcast** virtual microphone auto-detection for AI noise suppression

### Voice Commands

40+ built-in voice commands for hands-free control. Most commands have natural aliases (e.g., "scratch that" and "undo" both trigger undo).

| Category | Commands | What it does |
|----------|----------|--------------|
| **Undo/Redo** | "scratch that", "undo", "delete that", "delete last" | Undo last action |
| | "redo" | Redo last action |
| **Selection** | "select", "select word", "select that", "select last" | Select previous word |
| | "select all" | Select all text |
| | "select line" | Select current line |
| **Deletion** | "delete word", "backspace word" | Delete previous word |
| | "delete line", "clear line" | Delete current line |
| **Navigation** | "new line", "enter", "next line" | Insert new line |
| | "new paragraph", "next paragraph" | Insert blank line |
| | "go to start", "go to beginning" | Jump to document start |
| | "go to end" | Jump to document end |
| | "go up", "go down" | Move cursor up/down |
| **Clipboard** | "copy", "copy that" | Copy selection |
| | "paste", "paste that" | Paste (terminal-aware) |
| | "cut", "cut that" | Cut selection |
| **Formatting** | "tab", "indent" | Insert tab |
| | "outdent", "unindent" | Remove tab |
| **File** | "save", "save file", "save that" | Save file (Ctrl+S) |
| **Control** | "stop listening", "pause", "stop" | Pause dictation |

### Smart Typing

- **Auto-spacing** -- automatically adds spaces between utterances
- **Context-aware spacing reset** -- navigation and editing commands reset the space flag so text appears at the cursor without a leading space
- **Terminal-aware paste** -- automatically uses Ctrl+Shift+V in Windows Terminal, ConEmu, PuTTY, mintty, and other terminal emulators
- **Lossless clipboard** -- saves and restores your clipboard contents (full Unicode support) so dictation never overwrites what you copied
- **Enter key tracking** -- pressing Enter on your keyboard also resets auto-spacing for natural line-start behavior

### Visual Feedback

- **Always-on-top status indicator** -- small draggable window showing current state
- **Color-coded states**: green (LISTENING), orange (WORKING), gray (PAUSED)
- **System-wide hotkey**: Ctrl+Alt+V to toggle listening on/off
- **Audio feedback** -- beep tones on toggle (high pitch on, low pitch off)

### Reliability

- **Automatic recorder restart** on connection loss or repeated errors
- **Graceful shutdown** with resource cleanup on Ctrl+C
- **Log file** (`hushtype.log`) for diagnostics, truncated each session
- **Debounced hotkey** to prevent double-toggles

## Requirements

- **Windows 10 or 11** (uses Win32 APIs for system-wide input)
- **NVIDIA GPU with CUDA support** (RTX 20-series or newer recommended)
- **Microphone** (built-in, USB, or NVIDIA Broadcast virtual mic)
- **~4 GB VRAM** for the turbo model (~1 GB for tiny/base/small)
- **Python 3.10+** (only needed if running from source)

## Installation

### Option 1: Download the executable (easiest)

Download `hushtype.exe` from the [latest release](https://github.com/turqoisehex/hushtype/releases/latest) and double-click to run. No Python or setup required.

On first run, the Whisper model (~1.5 GB) downloads automatically. This is a one-time download. Your firewall may prompt you to allow the connection -- this is only for the model download. After that, all speech recognition runs locally on your GPU.

### Option 2: Run from source

Requires Python 3.10+ and an NVIDIA GPU with CUDA.

```bash
# 1. Install PyTorch with CUDA (check https://pytorch.org for your CUDA version)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# 2. Clone and install
git clone https://github.com/turqoisehex/hushtype.git
cd hushtype
pip install -r requirements.txt

# 3. Run
python hushtype.py
```

### NVIDIA Broadcast (optional)

If you have [NVIDIA Broadcast](https://www.nvidia.com/en-us/geforce/broadcasting/broadcast-app/), hushtype automatically detects and uses its virtual microphone for AI-powered noise and echo suppression. No configuration needed -- just make sure Broadcast is running.

## Usage

```
hushtype [options]

Options:
  --model MODEL        Whisper model: tiny, base, small, medium, large-v3, turbo (default: turbo)
  --silence SECONDS    Seconds of silence before finalizing speech (default: 2.5)
  --sensitivity VALUE  VAD sensitivity 0.0-1.0, higher = more sensitive (default: 0.55)
  --device NAME        Preferred mic name substring (e.g. --device ZOOM). Overrides NVIDIA Broadcast.
  --channel N          Audio channel on multi-channel devices, 1-indexed (default: 1)
  --verbose            Show detailed debug logging from the speech recognizer
  --offline            Disable all network access (model must already be cached)
  --cache-dir DIR      Custom HuggingFace cache directory for Whisper models
  --version            Show version and exit
  --help               Show help and exit
```

### Quick start

1. Run `hushtype.exe` (or `python hushtype.py`)
2. Wait for "Model loaded. Ready." (first run downloads the model)
3. A small status indicator appears in the bottom-right corner showing **PAUSED**
4. Press **Ctrl+Alt+V** -- indicator turns green, showing **LISTENING**
5. Speak naturally -- text appears wherever your cursor is
6. Say **"stop listening"** or press **Ctrl+Alt+V** again to pause
7. Press **Ctrl+C** in the terminal to quit

### Tuning speech detection

If speech is cutting off too early, increase the silence threshold:

```bash
hushtype --silence 3.0
```

If hushtype triggers on background noise, lower VAD sensitivity:

```bash
hushtype --sensitivity 0.4
```

For smaller/faster models (less accurate but lower VRAM usage):

```bash
hushtype --model small    # ~1 GB VRAM
hushtype --model tiny     # ~1 GB VRAM, fastest
```

### Using an existing model cache

If you already have Whisper models downloaded elsewhere, point hushtype to that directory:

```bash
hushtype --cache-dir "C:\path\to\huggingface"
```

## How It Works

1. **Silero VAD** continuously monitors the microphone for speech activity
2. When speech is detected, audio is streamed to **faster-whisper** (CTranslate2-optimized Whisper)
3. Transcribed text is matched against the **voice command table**
4. If no command matches, text is **typed via clipboard paste** (handles Unicode, instant)
5. **Auto-spacing** adds a leading space between consecutive utterances
6. The previous clipboard contents are **saved and restored** after each paste

## Building the Executable

The executable is built automatically by GitHub Actions when a version tag is pushed. To build locally:

```bash
pip install pyinstaller
pyinstaller hushtype.spec
# Output: dist/hushtype.exe
```

## Privacy

- **All speech recognition runs locally** on your GPU using faster-whisper
- **No audio data is sent to any server** -- ever
- **No telemetry, no analytics, no tracking**
- On first run, the Whisper model is downloaded from HuggingFace (the only network request)
- Use `--offline` to block all network access after the model is cached

## FAQ

**Q: Why Windows only?**
hushtype uses Win32 APIs (GetAsyncKeyState, GetForegroundWindow, win32clipboard) for system-wide hotkey detection, terminal window class identification, and clipboard management. These are Windows-specific. Cross-platform support is a possible future addition.

**Q: What GPU do I need?**
Any NVIDIA GPU with CUDA support. The turbo model uses ~4 GB VRAM. Smaller models (tiny, base, small) use ~1 GB. CPU-only mode is not currently supported.

**Q: My firewall is asking about hushtype -- is it safe?**
Yes. The only network request is to download the Whisper model from HuggingFace on first run (~1.5 GB). After that, hushtype runs fully offline. You can use `--offline` to verify no network access occurs.

**Q: Does it work with any microphone?**
Yes. Any Windows audio input device works, including USB audio interfaces (ZOOM, Focusrite, etc.) with multiple channels. If NVIDIA Broadcast is installed, hushtype automatically uses the Broadcast virtual microphone for AI noise suppression. Use `--device NAME` to select a specific mic, and `--channel N` to pick which input on a multi-channel interface.

**Q: Can I add custom voice commands?**
Not yet via config file, but the `VOICE_COMMANDS` dictionary in `hushtype.py` is straightforward to edit. Custom command support via config file is planned.

**Q: Why clipboard paste instead of simulated keystrokes?**
Clipboard paste handles Unicode characters, accented text, and special symbols that `SendKeys` or `pyautogui.write()` cannot type. It is also instantaneous regardless of text length. Your clipboard contents are automatically saved and restored after each paste.

**Q: Is my audio sent to the cloud?**
No. All speech recognition runs locally on your GPU using faster-whisper. No audio data leaves your machine. See the [Privacy](#privacy) section.

**Q: How do I stop hushtype?**
Say "stop listening" to pause dictation (press Ctrl+Alt+V to resume). Press Ctrl+C in the terminal window to quit entirely.

## Contributing

Contributions are welcome! This is a side project maintained in spare time, so please be patient with response times.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines. Check out issues labeled [`good first issue`](https://github.com/turqoisehex/hushtype/labels/good%20first%20issue) for beginner-friendly tasks.

## Keywords

voice dictation, speech to text, whisper, voice typing, dictation software, speech recognition, stt, voice input, nvidia gpu, cuda, windows voice dictation, real-time transcription, live transcription, voice commands, hands-free typing, accessibility, python speech to text, openai whisper, faster-whisper, voice control, dictation app, system-wide dictation, microphone to text, talk to type, voice to text windows, speech to text windows, gpu transcription, local speech recognition, offline speech to text, voice input method, whisper turbo, silero vad, realtime stt

## License

[MIT](LICENSE)
