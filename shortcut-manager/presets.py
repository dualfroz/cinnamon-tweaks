import shutil

_CANDIDATES = [
    ("Terminal", "gnome-terminal", "gnome-terminal"),
    ("File manager", "nemo", "nemo"),
    ("Lock screen", "cinnamon-screensaver-command", "cinnamon-screensaver-command --lock"),
    ("Screenshot - area", "flameshot", "flameshot gui"),
    ("Screenshot - full screen", "gnome-screenshot", "gnome-screenshot"),
    ("Web browser", "xdg-open", "xdg-open http://"),
    ("Mute volume toggle", "amixer", "amixer -q set Master toggle"),
    ("Text editor", "gedit", "gedit"),
]


def availablePresets():
    return [(label, command) for label, binary, command in _CANDIDATES if shutil.which(binary)]
