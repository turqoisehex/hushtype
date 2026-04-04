# Custom hook for webrtcvad — overrides the broken contrib hook.
# The contrib hook calls copy_metadata('webrtcvad') but the package is
# installed as 'webrtcvad-wheels', causing ImportErrorWhenRunningHook.

from PyInstaller.utils.hooks import copy_metadata

try:
    datas = copy_metadata('webrtcvad-wheels')
except Exception:
    datas = []
