# Contributing to hushtype

This is a side project maintained in spare time. Contributions are welcome -- but please be patient with response times.

## Development Setup

### Prerequisites

- **Windows 10 or 11** (hushtype uses Win32 APIs)
- **Python 3.10 - 3.12** (3.12 recommended)
- **NVIDIA GPU with CUDA support** (RTX 20-series or newer recommended)
- **CUDA Toolkit** matching your GPU driver
- **Microphone** for testing

### Local Development

```bash
# 1. Fork and clone the repo
git clone https://github.com/YOUR_USERNAME/hushtype.git
cd hushtype

# 2. Install PyTorch with CUDA (check https://pytorch.org for your CUDA version)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python hushtype.py
```

### Building the Executable Locally

```bash
pip install pyinstaller
pyinstaller hushtype.spec
# Output: dist/hushtype.exe
```

The CI workflow builds the exe automatically on tagged releases -- local builds are only needed for testing.

## How to Contribute

### Reporting Bugs

Use the [Bug Report](https://github.com/turqoisehex/hushtype/issues/new?template=bug_report.yml) issue template. Include:

- Steps to reproduce
- Expected vs actual behavior
- Your environment (Windows version, GPU, Python version)
- Any error output or logs (`hushtype.log`)

### Suggesting Features

Use the [Feature Request](https://github.com/turqoisehex/hushtype/issues/new?template=feature_request.yml) issue template. Describe the problem you're solving, not just the solution you want.

### Submitting Code

1. Fork the repo
2. Create a branch from `master`: `git checkout -b feat/your-feature`
3. Make changes with clear commits
4. Test with a real microphone and GPU
5. Submit a PR against `master`

### Branch Naming

- `feat/` -- new features
- `fix/` -- bug fixes
- `docs/` -- documentation
- `refactor/` -- code restructuring

## Architecture Notes

hushtype is a single-file application (`hushtype.py`). Key components:

- **AudioToTextRecorder** (RealtimeSTT) -- streaming speech-to-text engine
- **Voice command table** -- regex-matched commands with keyboard action callbacks
- **Clipboard paste system** -- saves/restores clipboard for Unicode text input
- **Status indicator** -- tkinter overlay window with state colors
- **Hotkey listener** -- Win32 GetAsyncKeyState polling for Ctrl+Alt+V

## Recognition

All contributors are recognized. We value bug reports, documentation, and community support -- not just code.

## Questions?

Open a [Discussion](https://github.com/turqoisehex/hushtype/discussions) or comment on a relevant issue.
