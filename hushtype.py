"""hushtype -- Real-time voice dictation for Windows.

GPU-accelerated speech-to-text using OpenAI Whisper, with voice commands,
smart auto-spacing, terminal-aware paste, and a visual status indicator.
Runs system-wide as an input method -- dictate into any application.

Usage:
    python hushtype.py              Start dictation (Ctrl+Alt+V to toggle)
    python hushtype.py --help       Show all options

https://github.com/turqoisehex/hushtype
"""

import os
import sys

# Ensure print() works in PyInstaller frozen exe (unbuffered stdout)
if getattr(sys, 'frozen', False):
    try:
        sys.stdout.reconfigure(line_buffering=True)
        sys.stderr.reconfigure(line_buffering=True)
    except Exception:
        pass

import multiprocessing
import argparse

# Suppress noisy hf_xet warning about optional download accelerator
import warnings
warnings.filterwarnings("ignore", message=".*hf_xet.*")

from RealtimeSTT import AudioToTextRecorder
import numpy as np
import pyautogui
import pyaudio
import re
import time
import threading
import logging
import ctypes
import winsound
import tkinter as tk
import win32clipboard

pyautogui.FAILSAFE = False

__version__ = "1.0.0"

# ---------------------------------------------------------------------------
# Logging setup -- truncated each session
# ---------------------------------------------------------------------------

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hushtype.log")
_file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
_file_handler.setFormatter(
    logging.Formatter('%(asctime)s %(levelname)s %(name)s: %(message)s'))
logging.getLogger().addHandler(_file_handler)
logging.getLogger().setLevel(logging.WARNING)


class _QuietFilter(logging.Filter):
    """Suppress noisy 'latency limit' messages from console (still logged to file)."""
    def filter(self, record):
        return "latency limit" not in record.getMessage()

for _h in logging.getLogger().handlers:
    if isinstance(_h, logging.StreamHandler) and not isinstance(_h, logging.FileHandler):
        _h.addFilter(_QuietFilter())
logging.getLogger("realtimestt").addFilter(_QuietFilter())

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

listening = False
recorder = None
last_toggle_time = 0
need_space_before = False
status_window = None
status_label = None

# CLI overrides -- populated by parse_args(), read by recorder_loop()
_cli_config = {
    'model': 'turbo', 'silence': 3.0, 'sensitivity': 0.4, 'channel': 1,
}

# Known Whisper hallucination phrases (appear on silence/noise).
HALLUCINATION_PHRASES = {
    "thank you", "thanks for watching", "i'm sorry",
    "you", "bye", "the end",
}

# Terminal window classes that need Ctrl+Shift+V instead of Ctrl+V
TERMINAL_CLASSES = {
    b"ConsoleWindowClass", b"CASCADIA_HOSTING_WINDOW_CLASS",
    b"mintty", b"VirtualConsoleClass", b"PuTTY",
}
user32 = ctypes.windll.user32

# ---------------------------------------------------------------------------
# Hotkey polling via GetAsyncKeyState (no keyboard library dependency)
# ---------------------------------------------------------------------------

VK_CONTROL = 0x11
VK_MENU = 0x12      # Alt
VK_V = 0x56
VK_RETURN = 0x0D
GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.restype = ctypes.c_short
GetAsyncKeyState.argtypes = [ctypes.c_int]

_hotkey_was_pressed = False
_enter_was_pressed = False


def poll_hotkey():
    """Poll Ctrl+Alt+V and Enter via GetAsyncKeyState every 50 ms."""
    global _hotkey_was_pressed, _enter_was_pressed, need_space_before

    ctrl = GetAsyncKeyState(VK_CONTROL) & 0x8000
    alt = GetAsyncKeyState(VK_MENU) & 0x8000
    v_key = GetAsyncKeyState(VK_V) & 0x8000
    hotkey_down = bool(ctrl and alt and v_key)
    if hotkey_down and not _hotkey_was_pressed:
        toggle()
    _hotkey_was_pressed = hotkey_down

    enter_down = bool(GetAsyncKeyState(VK_RETURN) & 0x8000)
    if enter_down and not _enter_was_pressed:
        need_space_before = False
    _enter_was_pressed = enter_down

    if status_window:
        status_window.after(50, poll_hotkey)


# ---------------------------------------------------------------------------
# Audio device discovery
# ---------------------------------------------------------------------------

def find_input_device(name_substring):
    """Find audio input device index by name substring, or None."""
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if (info['maxInputChannels'] > 0
                    and name_substring.lower() in info['name'].lower()):
                print(f"[OK] Using device {i}: {info['name']}")
                return i
    finally:
        p.terminate()
    return None


# ---------------------------------------------------------------------------
# Audio feed thread -- reads from mic, feeds to recorder
# ---------------------------------------------------------------------------

def audio_feed(device_index):
    """Read int16 mono audio from device and feed to recorder via feed_audio.

    Opens at 16 kHz mono int16 (proven to work on NVIDIA Broadcast).
    If mono fails, opens with native channels and extracts selected channel.
    """
    global recorder
    RATE = 16000
    CHUNK = 1024
    ch_select = _cli_config.get('channel', 1) - 1  # 1-indexed CLI -> 0-indexed

    while True:
        p = pyaudio.PyAudio()
        stream = None
        mono = True
        try:
            try:
                stream = p.open(
                    format=pyaudio.paInt16, channels=1, rate=RATE,
                    input=True, input_device_index=device_index,
                    frames_per_buffer=CHUNK)
            except Exception:
                info = p.get_device_info_by_index(device_index)
                ch = int(info['maxInputChannels'])
                mono = False
                stream = p.open(
                    format=pyaudio.paInt16, channels=ch, rate=RATE,
                    input=True, input_device_index=device_index,
                    frames_per_buffer=CHUNK)

            while True:
                data = stream.read(CHUNK, exception_on_overflow=False)
                if mono:
                    r = recorder
                    if r is not None:
                        r.feed_audio(data)
                else:
                    samples = np.frombuffer(data, dtype=np.int16)
                    ch_idx = min(ch_select, ch - 1)
                    selected = samples[ch_idx::ch].copy()
                    r = recorder
                    if r is not None:
                        r.feed_audio(selected)

        except Exception as e:
            logging.warning("Audio feed error: %s", e)
            print(f"[!] Audio feed error: {e}")
            time.sleep(2)
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            p.terminate()


# ---------------------------------------------------------------------------
# Clipboard paste (terminal-aware)
# ---------------------------------------------------------------------------

def is_terminal_foreground():
    hwnd = user32.GetForegroundWindow()
    class_name = ctypes.create_string_buffer(256)
    user32.GetClassNameA(hwnd, class_name, 256)
    return class_name.value in TERMINAL_CLASSES


def paste_from_clipboard():
    """Send Ctrl+V or Ctrl+Shift+V depending on whether target is a terminal."""
    if is_terminal_foreground():
        pyautogui.hotkey('ctrl', 'shift', 'v')
    else:
        pyautogui.hotkey('ctrl', 'v')


# ---------------------------------------------------------------------------
# Visual indicator
# ---------------------------------------------------------------------------

drag_start_x = 0
drag_start_y = 0


def create_status_window():
    global status_window, status_label
    status_window = tk.Tk()
    status_window.title("")
    status_window.attributes('-topmost', True)
    status_window.attributes('-alpha', 0.85)
    status_window.overrideredirect(True)

    sw = status_window.winfo_screenwidth()
    sh = status_window.winfo_screenheight()
    status_window.geometry(f"120x30+{sw - 140}+{sh - 75}")

    status_label = tk.Label(
        status_window, text="PAUSED",
        font=("Segoe UI", 11, "bold"),
        fg="white", bg="#666666", padx=10, pady=5)
    status_label.pack(fill=tk.BOTH, expand=True)

    status_label.bind('<Button-1>', _start_drag)
    status_label.bind('<B1-Motion>', _on_drag)
    return status_window


def _start_drag(event):
    global drag_start_x, drag_start_y
    drag_start_x = event.x
    drag_start_y = event.y


def _on_drag(event):
    x = status_window.winfo_x() + event.x - drag_start_x
    y = status_window.winfo_y() + event.y - drag_start_y
    status_window.geometry(f"+{x}+{y}")


def update_status(state):
    if status_label is None:
        return

    def do_update():
        if state == "paused":
            status_label.config(text="PAUSED", bg="#666666")
        elif state == "listening":
            status_label.config(text="LISTENING", bg="#2e7d32")
        elif state == "transcribing":
            status_label.config(text="WORKING", bg="#f57c00")

    if status_window:
        status_window.after(0, do_update)


# ---------------------------------------------------------------------------
# Recorder callbacks
# ---------------------------------------------------------------------------

def on_recording_start():
    if listening:
        update_status("listening")


def on_recording_stop():
    if listening:
        update_status("transcribing")


# ---------------------------------------------------------------------------
# Voice commands
# ---------------------------------------------------------------------------

def clean_command(text):
    """Remove punctuation and extra whitespace for command matching."""
    return re.sub(r'[^\w\s]', '', text).strip().lower()


VOICE_COMMANDS = {
    # Correction
    "scratch that":   lambda: pyautogui.hotkey('ctrl', 'z'),
    "delete that":    lambda: pyautogui.hotkey('ctrl', 'z'),
    "delete last":    lambda: pyautogui.hotkey('ctrl', 'z'),
    "select that":    lambda: pyautogui.hotkey('ctrl', 'shift', 'left'),
    "select last":    lambda: pyautogui.hotkey('ctrl', 'shift', 'left'),
    "select word":    lambda: pyautogui.hotkey('ctrl', 'shift', 'left'),
    "select":         lambda: pyautogui.hotkey('ctrl', 'shift', 'left'),
    "select all":     lambda: pyautogui.hotkey('ctrl', 'a'),
    "undo":           lambda: pyautogui.hotkey('ctrl', 'z'),
    "undo that":      lambda: pyautogui.hotkey('ctrl', 'z'),
    "redo":           lambda: pyautogui.hotkey('ctrl', 'y'),
    "redo that":      lambda: pyautogui.hotkey('ctrl', 'y'),
    "delete word":    lambda: pyautogui.hotkey('ctrl', 'backspace'),
    "backspace word": lambda: pyautogui.hotkey('ctrl', 'backspace'),
    # Navigation
    "new line":       lambda: pyautogui.press('enter'),
    "newline":        lambda: pyautogui.press('enter'),
    "next line":      lambda: pyautogui.press('enter'),
    "enter":          lambda: pyautogui.press('enter'),
    "go to start":    lambda: pyautogui.hotkey('ctrl', 'home'),
    "go to beginning": lambda: pyautogui.hotkey('ctrl', 'home'),
    "go to end":      lambda: pyautogui.hotkey('ctrl', 'end'),
    "go up":          lambda: pyautogui.press('up'),
    "go down":        lambda: pyautogui.press('down'),
    # Clipboard
    "copy":           lambda: pyautogui.hotkey('ctrl', 'c'),
    "copy that":      lambda: pyautogui.hotkey('ctrl', 'c'),
    "paste":          paste_from_clipboard,
    "paste that":     paste_from_clipboard,
    "cut":            lambda: pyautogui.hotkey('ctrl', 'x'),
    "cut that":       lambda: pyautogui.hotkey('ctrl', 'x'),
    # Formatting
    "tab":            lambda: pyautogui.press('tab'),
    "indent":         lambda: pyautogui.press('tab'),
    "outdent":        lambda: pyautogui.hotkey('shift', 'tab'),
    "unindent":       lambda: pyautogui.hotkey('shift', 'tab'),
    # Special
    "save":           lambda: pyautogui.hotkey('ctrl', 's'),
    "save file":      lambda: pyautogui.hotkey('ctrl', 's'),
    "save that":      lambda: pyautogui.hotkey('ctrl', 's'),
}

_MULTI_STEP = {
    "select line":    [('press', 'home'), ('hotkey', 'shift', 'end')],
    "delete line":    [('press', 'home'), ('hotkey', 'shift', 'end'), ('press', 'delete')],
    "clear line":     [('press', 'home'), ('hotkey', 'shift', 'end'), ('press', 'delete')],
    "new paragraph":  [('press', 'enter'), ('press', 'enter')],
    "next paragraph": [('press', 'enter'), ('press', 'enter')],
}

# Commands that don't change cursor/text state -- preserve need_space_before.
_NO_RESET_CMDS = {"copy", "copy that", "save", "save file", "save that"}


def _dispatch_command(cmd):
    """Execute a voice command. Returns True if handled."""
    if cmd in VOICE_COMMANDS:
        VOICE_COMMANDS[cmd]()
        return True
    if cmd in _MULTI_STEP:
        for step in _MULTI_STEP[cmd]:
            action, *args = step
            getattr(pyautogui, action)(*args)
        return True
    if cmd in ("stop listening", "pause", "stop"):
        toggle()
        return True
    return False


# ---------------------------------------------------------------------------
# Text processing
# ---------------------------------------------------------------------------

def process(text):
    global need_space_before

    t = text.strip()
    if not t:
        return
    if not listening:
        return
    if time.time() - last_toggle_time < 0.5:
        return

    update_status("listening")

    if t.lower().rstrip('.!?,') in HALLUCINATION_PHRASES:
        return

    cmd = clean_command(t)

    # Voice command dispatch
    if _dispatch_command(cmd):
        if cmd not in _NO_RESET_CMDS:
            need_space_before = False
        return

    # Default: type the text via clipboard
    prefix = " " if need_space_before else ""

    old_clip = None
    try:
        win32clipboard.OpenClipboard()
        try:
            old_clip = win32clipboard.GetClipboardData(
                win32clipboard.CF_UNICODETEXT)
        except TypeError:
            pass
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        pass

    try:
        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(
                win32clipboard.CF_UNICODETEXT, prefix + t)
        finally:
            win32clipboard.CloseClipboard()
    except Exception:
        return  # clipboard locked -- skip silently

    need_space_before = True
    paste_from_clipboard()
    time.sleep(0.03)

    if old_clip is not None:
        try:
            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(
                    win32clipboard.CF_UNICODETEXT, old_clip)
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Toggle listening
# ---------------------------------------------------------------------------

def toggle():
    global listening, last_toggle_time, need_space_before
    if time.time() - last_toggle_time < 0.3:
        return
    listening = not listening
    last_toggle_time = time.time()
    if listening:
        need_space_before = False
        clear_audio_buffer()
        print("\n[LISTENING]")
        update_status("listening")
        threading.Thread(target=lambda: winsound.Beep(523, 80),
                         daemon=True).start()
    else:
        print("\n[PAUSED]")
        update_status("paused")
        threading.Thread(target=lambda: winsound.Beep(440, 80),
                         daemon=True).start()
        if recorder:
            try:
                recorder.interrupt_stop_event.set()
            except AttributeError:
                pass


# ---------------------------------------------------------------------------
# Audio buffer management
# ---------------------------------------------------------------------------

def clear_audio_buffer():
    """Drain any audio that accumulated in the recorder while paused."""
    if recorder is None:
        return
    try:
        if hasattr(recorder, 'audio_queue'):
            while not recorder.audio_queue.empty():
                try:
                    recorder.audio_queue.get_nowait()
                except Exception:
                    break
        if hasattr(recorder, 'frames'):
            recorder.frames.clear()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Recorder management
# ---------------------------------------------------------------------------

def create_recorder(input_device_index):
    """Create a fresh AudioToTextRecorder instance."""
    return AudioToTextRecorder(
        model=_cli_config['model'],
        language="en",
        device="cuda",
        compute_type="auto",
        use_microphone=False,           # we feed audio ourselves
        silero_sensitivity=_cli_config['sensitivity'],
        silero_use_onnx=True,
        post_speech_silence_duration=_cli_config['silence'],
        min_length_of_recording=0.5,
        early_transcription_on_silence=300,
        normalize_audio=True,
        spinner=False,
        on_recording_start=on_recording_start,
        on_recording_stop=on_recording_stop,
    )


def _restart_recorder(device_index, reason):
    """Shutdown and recreate the recorder. Returns True on success."""
    global recorder
    _file_handler.setLevel(logging.CRITICAL)
    try:
        recorder.shutdown()
    except Exception:
        pass
    time.sleep(2)
    try:
        recorder = create_recorder(device_index)
        _file_handler.setLevel(logging.WARNING)
        print("[OK] Recorder restarted.\n")
        logging.warning("Recorder restarted after: %s", reason)
        return True
    except Exception as e:
        _file_handler.setLevel(logging.WARNING)
        logging.exception("Recorder restart failed")
        print(f"[ERR] Restart failed: {e}")
        print("      Retrying in 5 seconds...")
        time.sleep(5)
        return False


# ---------------------------------------------------------------------------
# Recorder loop
# ---------------------------------------------------------------------------

def recorder_loop(device_index):
    global recorder

    print("[...] Loading Whisper model (GPU)...")

    # Device selection: --device > NVIDIA Broadcast > system default
    input_device = device_index
    if _cli_config.get('device'):
        explicit = find_input_device(_cli_config['device'])
        if explicit is not None:
            input_device = explicit
        else:
            print(f"[!] Device matching '{_cli_config['device']}' not found")

    recorder = create_recorder(input_device)
    print("[OK] Model loaded. Ready.\n")

    # Start audio feed thread
    threading.Thread(target=audio_feed, args=(input_device,),
                     daemon=True).start()

    was_listening = False
    error_count = 0
    while True:
        try:
            if listening:
                if not was_listening:
                    clear_audio_buffer()
                was_listening = True
                recorder.text(process)
                error_count = 0
            else:
                was_listening = False
                time.sleep(0.1)
        except (BrokenPipeError, ConnectionError, EOFError, OSError) as e:
            logging.exception("Recorder connection lost")
            print(f"\n[!] Recorder connection lost: {e}")
            if _restart_recorder(input_device, str(e)):
                error_count = 0
                was_listening = False
        except Exception as e:
            error_count += 1
            logging.warning("Recorder error (%d/5): %s", error_count, e)
            if error_count >= 5:
                logging.exception("Too many errors, restarting recorder")
                print(f"\n[!] Too many errors ({e}) -- restarting...")
                if _restart_recorder(input_device, str(e)):
                    error_count = 0
                    was_listening = False
            else:
                print(f"[!] Error: {e}")
                time.sleep(0.5)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        prog="hushtype",
        description=(
            "Real-time voice dictation for Windows. "
            "GPU-accelerated speech-to-text powered by OpenAI Whisper, "
            "with 40+ voice commands, smart auto-spacing, terminal-aware "
            "paste, and a visual status indicator."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--model", default="turbo",
        help="Whisper model size: tiny, base, small, medium, large-v3, "
             "turbo (default: turbo)",
    )
    parser.add_argument(
        "--silence", type=float, default=3.0,
        help="Seconds of silence before finalizing speech (default: 3.0)",
    )
    parser.add_argument(
        "--sensitivity", type=float, default=0.4,
        help="VAD sensitivity 0.0-1.0, higher = more sensitive (default: 0.4)",
    )
    parser.add_argument(
        "--device",
        help="Preferred mic name substring (e.g. --device ZOOM). "
             "Overrides NVIDIA Broadcast.",
    )
    parser.add_argument(
        "--channel", type=int, default=1,
        help="Audio channel on multi-channel devices, 1-indexed (default: 1)",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Show detailed debug logging from the speech recognizer",
    )
    parser.add_argument(
        "--offline", action="store_true",
        help="Disable all network access (model must already be cached)",
    )
    parser.add_argument(
        "--cache-dir",
        help="HuggingFace cache directory for Whisper models",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    print("=" * 50)
    print(f"hushtype v{__version__} -- Voice Dictation")
    print("=" * 50)
    print("\nPress Ctrl+Alt+V to toggle listening")
    print("Press Ctrl+C to quit")
    print("\nCommands: scratch that, delete word, select, new line,")
    print("          undo, redo, copy, paste, save, stop listening\n")

    if args.offline:
        os.environ["HF_HUB_OFFLINE"] = "1"

    if args.cache_dir:
        os.environ["HF_HOME"] = args.cache_dir

    _cli_config['model'] = args.model
    _cli_config['silence'] = args.silence
    _cli_config['sensitivity'] = args.sensitivity
    _cli_config['device'] = args.device
    _cli_config['channel'] = args.channel
    _cli_config['verbose'] = args.verbose

    if args.verbose:
        logging.getLogger("realtimestt").setLevel(logging.DEBUG)
        _console = logging.StreamHandler()
        _console.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s'))
        logging.getLogger("realtimestt").addHandler(_console)

    # Find default device before starting
    device = find_input_device("NVIDIA Broadcast")
    if device is None:
        print("[!] NVIDIA Broadcast not found, using system default")

    root = create_status_window()

    # Start hotkey polling (runs inside tkinter main loop)
    poll_hotkey()

    # Start recorder in background thread
    recorder_thread = threading.Thread(
        target=recorder_loop, args=(device,), daemon=True)
    recorder_thread.start()

    try:
        root.mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        print("\nExiting")
        if recorder:
            try:
                recorder.shutdown()
            except Exception:
                pass


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()
