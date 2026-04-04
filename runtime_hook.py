"""PyInstaller runtime hook — mock unused RealtimeSTT dependencies.

RealtimeSTT imports pvporcupine, openwakeword, and halo unconditionally
at module level, even when those features aren't used. hushtype doesn't
use wake words (pvporcupine, openwakeword) or terminal spinners (halo).
Mocking these avoids bundling their native binaries and resource files.
webrtcvad is bundled normally via a custom PyInstaller hook.
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

# --- webrtcvad is now bundled (custom hook in hooks/ fixes the broken
# contrib hook).  No mock needed.

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
