# Changelog

All notable changes to hushtype will be documented in this file.

## [1.0.0] - 2026-03-27

### Added

- Real-time voice dictation with OpenAI Whisper (turbo model, GPU-accelerated)
- Silero VAD with ONNX optimization for fast, accurate speech boundary detection
- 40+ voice commands: editing, navigation, clipboard, formatting, and control
- Smart auto-spacing between utterances with context-aware reset
- Terminal-aware paste (Ctrl+Shift+V in terminals, Ctrl+V elsewhere)
- Lossless clipboard save/restore (preserves Unicode clipboard contents)
- NVIDIA Broadcast virtual microphone auto-detection for AI noise suppression
- Whisper hallucination filtering (strips ghost phrases from silence/noise)
- Visual always-on-top status indicator (draggable, color-coded: green/orange/gray)
- Ctrl+Alt+V system-wide hotkey to toggle listening on/off
- Enter key detection to reset auto-spacing on new lines
- Configurable Whisper model, VAD sensitivity, and silence duration via CLI
- Automatic recorder restart on connection loss with retry logic
- Graceful shutdown with resource cleanup
