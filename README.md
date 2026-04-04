# hushtype

[![Release](https://img.shields.io/github/v/release/turqoisehex/hushtype)](https://github.com/turqoisehex/hushtype/releases/latest)
[![License](https://img.shields.io/github/license/turqoisehex/hushtype)](LICENSE)
[![Stars](https://img.shields.io/github/stars/turqoisehex/hushtype?style=social)](https://github.com/turqoisehex/hushtype)

**Real-time voice dictation for Windows** -- type anywhere with your voice using GPU-accelerated OpenAI Whisper speech-to-text.

hushtype turns your microphone into a keyboard. Press **Ctrl+Alt+V** to start dictating into any application -- text editors, browsers, terminals, chat apps, IDEs, email. All processing runs locally on your GPU. No audio data ever leaves your machine.

## Download

**[Download hushtype.exe](https://github.com/turqoisehex/hushtype/releases/latest)** -- standalone Windows executable, no Python or setup required.

> **First time running?** Windows may show a SmartScreen warning because the exe is not code-signed. Right-click the downloaded file, select **Properties**, check **Unblock** at the bottom of the General tab, and click OK. You only need to do this once.

On first launch, the Whisper speech model (~1.5 GB) downloads automatically. This is a one-time download -- after that, hushtype runs fully offline.

### What you need

- **Windows 10 or 11**
- **NVIDIA GPU with CUDA support** (RTX 20-series or newer recommended, ~4 GB VRAM)
- **A microphone** (built-in, USB, or [NVIDIA Broadcast](https://www.nvidia.com/en-us/geforce/broadcasting/broadcast-app/) virtual mic for AI noise suppression)

## Quick Start

1. Run `hushtype.exe`
2. Wait for **"Model loaded. Ready."** (first run downloads the model)
3. A small status indicator appears showing **PAUSED**
4. Press **Ctrl+Alt+V** -- indicator turns green, showing **LISTENING**
5. Speak naturally -- text appears wherever your cursor is
6. Say **"stop listening"** or press **Ctrl+Alt+V** again to pause
7. Press **Ctrl+C** in the terminal to quit

## Voice Commands

40+ built-in voice commands for hands-free control. Most have natural aliases (e.g., "scratch that" and "undo" both work).

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

## Features

- **OpenAI Whisper** speech-to-text with NVIDIA CUDA GPU acceleration
- **Silero VAD** (Voice Activity Detection) with ONNX optimization for low-latency detection
- **Auto-spacing** between utterances with context-aware resets after commands
- **Terminal-aware paste** -- uses Ctrl+Shift+V in Windows Terminal, ConEmu, PuTTY, mintty
- **Lossless clipboard** -- saves and restores your clipboard so dictation never overwrites it
- **Hallucination filtering** -- strips known Whisper ghost phrases (silence artifacts)
- **NVIDIA Broadcast** auto-detection for AI noise and echo suppression
- **Always-on-top status indicator** -- color-coded: green (LISTENING), orange (WORKING), gray (PAUSED)
- **Automatic recovery** -- restarts the recorder on connection loss or repeated errors

## Options

```
hushtype [options]

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

### Tuning speech detection

If speech is cutting off too early, increase the silence threshold:

```bash
hushtype --silence 3.0
```

If hushtype triggers on background noise, lower VAD sensitivity:

```bash
hushtype --sensitivity 0.4
```

For lower VRAM usage (less accurate but faster):

```bash
hushtype --model small    # ~1 GB VRAM
hushtype --model tiny     # ~1 GB VRAM, fastest
```

## Running from Source

If you prefer running from source instead of the exe:

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

## How It Works

1. **Silero VAD** monitors the microphone for speech activity
2. When speech is detected, audio streams to **faster-whisper** (CTranslate2-optimized Whisper)
3. Transcribed text is matched against the voice command table
4. If no command matches, text is typed via clipboard paste (handles Unicode, instant)
5. Auto-spacing adds a leading space between consecutive utterances
6. The previous clipboard contents are saved and restored after each paste

## Privacy

- **All speech recognition runs locally** on your GPU using faster-whisper
- **No audio data is sent to any server** -- ever
- **No telemetry, no analytics, no tracking**
- The Whisper model downloads from HuggingFace on first run (the only network request)
- Use `--offline` to block all network access after the model is cached

## FAQ

**Q: Why Windows only?**
hushtype uses Win32 APIs for system-wide hotkey detection, terminal identification, and clipboard management. Cross-platform support is a possible future addition.

**Q: What GPU do I need?**
Any NVIDIA GPU with CUDA support. The turbo model uses ~4 GB VRAM. Smaller models (tiny, base, small) use ~1 GB. CPU-only mode is not currently supported.

**Q: My firewall is asking about hushtype -- is it safe?**
Yes. The only network request is the one-time Whisper model download from HuggingFace (~1.5 GB). After that, hushtype runs fully offline. Use `--offline` to verify.

**Q: Does it work with any microphone?**
Yes. Any Windows audio input device works, including multi-channel USB interfaces (ZOOM, Focusrite, etc.). Use `--device NAME` to pick a specific mic and `--channel N` to select a channel.

**Q: Can I add custom voice commands?**
Not yet via config file, but the `VOICE_COMMANDS` dictionary in `hushtype.py` is straightforward to edit. Custom command support via config file is planned.

**Q: Why clipboard paste instead of simulated keystrokes?**
Clipboard paste handles Unicode, accented text, and special symbols that simulated keystrokes cannot type. It is also instantaneous regardless of text length. Your clipboard is automatically saved and restored.

**Q: How do I stop hushtype?**
Say "stop listening" to pause dictation (press Ctrl+Alt+V to resume). Press Ctrl+C in the terminal to quit entirely.

## Building the Executable

The exe is built automatically by GitHub Actions when a version tag is pushed. To build locally:

```bash
pip install pyinstaller
pyinstaller hushtype.spec
# Output: dist/hushtype.exe
```

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines. Check out issues labeled [`good first issue`](https://github.com/turqoisehex/hushtype/labels/good%20first%20issue) for beginner-friendly tasks.

## Keywords

voice dictation, speech to text, whisper, voice typing, dictation software, speech recognition, stt, voice input, nvidia gpu, cuda, windows voice dictation, real-time transcription, live transcription, voice commands, hands-free typing, accessibility, python speech to text, openai whisper, faster-whisper, voice control, dictation app, system-wide dictation, microphone to text, talk to type, voice to text windows, speech to text windows, gpu transcription, local speech recognition, offline speech to text, voice input method, whisper turbo, silero vad, realtime stt

## License

[MIT](LICENSE)
