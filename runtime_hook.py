"""PyInstaller runtime hook — mock unused RealtimeSTT dependencies.

RealtimeSTT imports pvporcupine, openwakeword, webrtcvad, and halo
unconditionally at module level, even when those features aren't used.
hushtype uses Silero VAD (not webrtcvad), no wake words (not pvporcupine
or openwakeword), and no spinner (not halo). Mocking these avoids
bundling their native binaries and resource files, which break in
PyInstaller's temp directory structure.
"""

import sys
import types


def _mock_module(name, attrs=None):
    """Register a fake module so `import name` succeeds."""
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# --- pvporcupine (wake word detection — not used) ---
_mock_module('pvporcupine', {
    'create': lambda **kw: None,
    'KEYWORD_PATHS': {},
    'KEYWORDS': set(),
})

# --- openwakeword (wake word detection — not used) ---
_oww = _mock_module('openwakeword')
_oww_model = _mock_module('openwakeword.model', {
    'Model': type('Model', (), {'__init__': lambda self, **kw: None}),
})
_oww.model = _oww_model

# --- webrtcvad (hushtype uses Silero VAD instead) ---
_mock_vad_cls = type('Vad', (), {
    '__init__': lambda self, mode=None: None,
    'set_mode': lambda self, mode: None,
    'is_speech': lambda self, buf, sample_rate, length=None: False,
})
_mock_module('webrtcvad', {'Vad': _mock_vad_cls})

# --- halo (terminal spinner — hushtype sets spinner=False) ---
_mock_halo_cls = type('Halo', (), {
    '__init__': lambda self, **kw: None,
    'start': lambda self: self,
    'stop': lambda self: None,
    'succeed': lambda self, text='': None,
    'fail': lambda self, text='': None,
    '__enter__': lambda self: self,
    '__exit__': lambda self, *a: None,
})
_mock_module('halo', {'Halo': _mock_halo_cls})
