"""
Backend for reading/writing Cinnamon custom keyboard shortcuts.

Cinnamon (like GNOME) stores custom shortcuts as a relocatable schema:
each shortcut lives at /org/cinnamon/desktop/keybindings/custom-keybindings/customN/
under the "org.cinnamon.desktop.keybindings.custom-keybinding" schema, with
three keys: name, command, binding (an array of accelerator strings, in
practice always a single entry). The top-level
"org.cinnamon.desktop.keybindings" schema holds "custom-list", the array of
customN ids Cinnamon actually reads at login. Writing straight to gsettings
is enough to make the shortcut live system-wide - no daemon or restart
needed, Cinnamon's keybinding manager watches these keys.
"""

import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gio, Gtk

LIST_SCHEMA = "org.cinnamon.desktop.keybindings"
ITEM_SCHEMA = "org.cinnamon.desktop.keybindings.custom-keybinding"
ITEM_PATH_ROOT = "/org/cinnamon/desktop/keybindings/custom-keybindings/"

CONFLICT_SCHEMAS = [
    "org.cinnamon.desktop.keybindings",
    "org.cinnamon.desktop.keybindings.wm",
    "org.cinnamon.desktop.keybindings.media-keys",
    "org.gnome.desktop.wm.keybindings",
    "org.cinnamon.muffin.keybindings",
]

IGNORED_KEYVALS = {
    "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
    "Super_L", "Super_R", "Meta_L", "Meta_R", "Caps_Lock", "Num_Lock",
    "ISO_Level3_Shift",
}


class Shortcut:
    def __init__(self, customId, name, command, binding):
        self.customId = customId
        self.name = name
        self.command = command
        self.binding = binding

    def label(self):
        if not self.binding:
            return "(unset)"
        keyval, mods = Gtk.accelerator_parse(self.binding)
        if not keyval:
            return self.binding
        return Gtk.accelerator_get_label(keyval, mods)


def _itemSettings(customId):
    return Gio.Settings.new_with_path(ITEM_SCHEMA, ITEM_PATH_ROOT + customId + "/")


def listShortcuts():
    listSettings = Gio.Settings.new(LIST_SCHEMA)
    ids = list(listSettings.get_strv("custom-list"))
    shortcuts = []
    for customId in ids:
        item = _itemSettings(customId)
        binding = item.get_strv("binding")
        shortcuts.append(Shortcut(
            customId,
            item.get_string("name"),
            item.get_string("command"),
            binding[0] if binding else "",
        ))
    return shortcuts


def _existingIndices():
    listSettings = Gio.Settings.new(LIST_SCHEMA)
    indices = set()
    for customId in listSettings.get_strv("custom-list"):
        if customId.startswith("custom") and customId[6:].isdigit():
            indices.add(int(customId[6:]))
    try:
        raw = subprocess.run(
            ["dconf", "list", ITEM_PATH_ROOT],
            capture_output=True, text=True, check=True,
        ).stdout
        for line in raw.splitlines():
            entry = line.strip().rstrip("/")
            if entry.startswith("custom") and entry[6:].isdigit():
                indices.add(int(entry[6:]))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return indices


def _nextCustomId():
    used = _existingIndices()
    nextIndex = 0
    while nextIndex in used:
        nextIndex += 1
    return f"custom{nextIndex}"


def addShortcut(name, command, binding):
    customId = _nextCustomId()
    item = _itemSettings(customId)
    item.set_string("name", name)
    item.set_string("command", command)
    item.set_strv("binding", [binding])

    listSettings = Gio.Settings.new(LIST_SCHEMA)
    ids = list(listSettings.get_strv("custom-list"))
    ids.append(customId)
    listSettings.set_strv("custom-list", ids)
    return customId


def updateShortcut(customId, name, command, binding):
    item = _itemSettings(customId)
    item.set_string("name", name)
    item.set_string("command", command)
    item.set_strv("binding", [binding])


def deleteShortcut(customId):
    listSettings = Gio.Settings.new(LIST_SCHEMA)
    ids = [existingId for existingId in listSettings.get_strv("custom-list") if existingId != customId]
    listSettings.set_strv("custom-list", ids)
    try:
        subprocess.run(
            ["dconf", "reset", "-f", ITEM_PATH_ROOT + customId + "/"],
            capture_output=True, check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass


def findConflicts(binding, excludeCustomId=None):
    if not binding:
        return []
    conflicts = []
    for shortcut in listShortcuts():
        if shortcut.customId == excludeCustomId:
            continue
        if shortcut.binding == binding:
            conflicts.append(f"custom shortcut \"{shortcut.name}\"")

    for schemaId in CONFLICT_SCHEMAS:
        settings = Gio.Settings.new(schemaId)
        for key in settings.list_keys():
            value = settings.get_value(key)
            if value.get_type_string() != "as":
                continue
            if binding in value.unpack():
                conflicts.append(f"system shortcut \"{key}\" ({schemaId})")
    return conflicts


def keyEventToAccelerator(keyval, state):
    keyvalName = Gtk.accelerator_name(keyval, 0)
    if keyvalName in IGNORED_KEYVALS:
        return None
    mask = state & Gtk.accelerator_get_default_mod_mask()
    accel = Gtk.accelerator_name(keyval, mask)
    if not accel or not Gtk.accelerator_valid(keyval, mask):
        return None
    return accel
