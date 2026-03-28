# hushtype

**Real-time voice dictation for Windows** -- type anywhere with your voice using GPU-accelerated OpenAI Whisper speech-to-text.

hushtype is a system-wide voice typing tool that turns your microphone into a keyboard. Press **Ctrl+Alt+V** to start dictating into any application -- text editors, browsers, terminals, chat apps, IDEs, email. It runs silently in the background with a minimal status indicator and supports 40+ voice commands for editing, navigation, and formatting.

Unlike transcription tools that process pre-recorded audio files, hushtype is a **live input method** -- speech appears as typed text in real time, wherever your cursor is.

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

Over 40 built-in voice commands for hands-free control:

| Category | Commands |
|----------|----------|
| **Editing** | "scratch that", "undo", "redo", "delete word", "delete line", "select word", "select line", "select all" |
| **Navigation** | "new line", "enter", "go to start", "go to end", "go up", "go down" |
| **Clipboard** | "copy", "paste", "cut" |
| **Formatting** | "tab", "indent", "outdent", "new paragraph" |
| **File** | "save" |
| **Control** | "stop listening", "pause" |

### Smart Typing

- **Auto-spacing** -- automatically adds spaces between utterances
- **Context-aware spacing reset** -- navigation commands reset the space flag so text appears at the cursor without a leading space
- **Terminal-aware paste** -- automatically uses Ctrl+Shift+V in Windows Terminal, ConEmu, PuTTY, mintty, and other terminal emulators
- **Lossless clipboard** -- saves and restores your clipboard contents (full Unicode support) so dictation never overwrites what you copied
- **Enter key tracking** -- pressing Enter resets auto-spacing for natural line-start behavior

### Visual Feedback

- **Always-on-top status indicator** -- small draggable window showing current state
- **Color-coded states**: green (LISTENING), orange (WORKING), gray (PAUSED)
- **System-wide hotkey**: Ctrl+Alt+V to toggle listening on/off
- **Audio feedback** -- beep tones on toggle (523 Hz on, 440 Hz off)

### Reliability

- **Automatic recorder restart** on connection loss or repeated errors
- **Graceful shutdown** with resource cleanup on Ctrl+C
- **Log file** for diagnostics (truncated each session)
- **Debounced hotkey** to prevent double-toggles

## Requirements

- **Windows 10/11** (system-wide input method uses Win32 APIs)
- **NVIDIA GPU** with CUDA support (RTX 20-series or newer recommended)
- **Python 3.10+** (for running from source)
- **Microphone** (or NVIDIA Broadcast virtual mic for AI noise suppression)

## Installation

### Option 1: Download the executable (easiest)

Download `hushtype.exe` from [Releases](https://github.com/turqoisehex/hushtype/releases/latest) and double-click to run. No Python or setup required.

On first run, the Whisper model (~1.5 GB) downloads automatically. This is a one-time download -- after that, all speech recognition runs locally on your GPU. No audio data ever leaves your machine.

### Option 2: Install from source

Requires Python 3.10+ and an NVIDIA GPU with CUDA.

```bash
# Install PyTorch with CUDA first (check https://pytorch.org for your CUDA version)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

git clone https://github.com/turqoisehex/hushtype.git
cd hushtype
pip install -r requirements.txt
python hushtype.py
```

### Option 3: pip install

```bash
pip install git+https://github.com/turqoisehex/hushtype.git
hushtype
```

### NVIDIA Broadcast (optional)

If you have [NVIDIA Broadcast](https://www.nvidia.com/en-us/geforce/broadcasting/broadcast-app/), hushtype automatically detects and uses its virtual microphone for AI-powered noise and echo suppression. No configuration needed.

## Usage

```
hushtype [options]

Options:
  --model MODEL        Whisper model: tiny, base, small, medium, large-v3, turbo (default: turbo)
  --silence SECONDS    Seconds of silence before finalizing speech (default: 2.5)
  --sensitivity VALUE  VAD sensitivity 0.0-1.0, higher = more sensitive (default: 0.55)
  --offline            Disable all network access (model must already be cached)
  --cache-dir DIR      Custom HuggingFace cache directory for Whisper models
  --version            Show version and exit
  --help               Show help and exit
```

### Quick start

1. Run `hushtype.exe` (or `python hushtype.py`)
2. A small status indicator appears in the bottom-right corner showing **PAUSED**
3. Press **Ctrl+Alt+V** -- indicator turns green, showing **LISTENING**
4. Speak naturally -- text appears wherever your cursor is
5. Say **"stop listening"** or press **Ctrl+Alt+V** again to pause

### Tuning speech detection

If speech is cutting off too early, increase `--silence`:

```bash
hushtype --silence 3.0
```

If hushtype triggers on background noise, lower `--sensitivity`:

```bash
hushtype --sensitivity 0.4
```

For smaller/faster models (less accurate but lower VRAM):

```bash
hushtype --model small
```

## How It Works

1. **Silero VAD** continuously monitors the microphone for speech activity
2. When speech is detected, audio is streamed to **faster-whisper** (CTranslate2-optimized Whisper)
3. Transcribed text is matched against the **voice command table** (40+ commands)
4. If no command matches, text is **typed via clipboard paste** (handles Unicode, instant)
5. **Auto-spacing** adds a leading space between consecutive utterances
6. The previous clipboard contents are **saved and restored** after each paste

## Building from Source

```bash
pip install pyinstaller
pyinstaller hushtype.spec
# Output: dist/hushtype.exe
```

## FAQ

**Q: Why Windows only?**
hushtype uses Win32 APIs (GetAsyncKeyState, GetForegroundWindow, win32clipboard) for system-wide hotkey detection, terminal window class identification, and clipboard management. These are Windows-specific. Cross-platform support is a possible future addition.

**Q: What GPU do I need?**
Any NVIDIA GPU with CUDA support. The turbo model uses ~4 GB VRAM. Smaller models (tiny, base, small) work with less VRAM. CPU-only mode is not currently supported.

**Q: Does it work with any microphone?**
Yes. It works with any Windows audio input device. If NVIDIA Broadcast is installed, it automatically uses the Broadcast virtual microphone for AI noise suppression.

**Q: Can I add custom voice commands?**
Not yet via config -- but the `VOICE_COMMANDS` dictionary in `hushtype.py` is straightforward to edit. Custom command support via config file is planned.

**Q: Why clipboard paste instead of simulated keystrokes?**
Clipboard paste handles Unicode characters, accented text, and special symbols that `SendKeys` or `pyautogui.write()` cannot type. It is also instantaneous regardless of text length.

**Q: Is my audio sent to the cloud?**
No. All speech recognition runs locally on your GPU using faster-whisper. No audio data leaves your machine.

## Keywords

voice dictation, speech to text, whisper, voice typing, dictation software, speech recognition, stt, voice input, nvidia gpu, cuda, windows voice dictation, real-time transcription, voice commands, hands-free typing, accessibility, python speech to text, openai whisper, faster-whisper, voice control, dictation app, system-wide dictation, microphone to text, talk to type, voice to text windows

## License

[MIT](LICENSE)
