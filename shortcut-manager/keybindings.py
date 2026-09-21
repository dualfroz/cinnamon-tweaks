import re
import subprocess
import sys

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

MODIFIER_ALIASES = {
    "control": "control", "ctrl": "control", "ctl": "control", "primary": "control",
    "shift": "shift", "shft": "shift",
    "alt": "alt", "mod1": "alt",
    "super": "super", "mod4": "super",
}

missingSchemasReported = set()


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


def normalizeAccelerator(binding):
    if not binding:
        return None
    modifiers = re.findall(r"<([^<>]+)>", binding)
    keyName = re.sub(r"<[^<>]+>", "", binding).strip()
    if not keyName:
        return None
    normalizedModifiers = frozenset(MODIFIER_ALIASES.get(name.lower(), name.lower()) for name in modifiers)
    return normalizedModifiers, keyName.lower()


def systemBindings(schemaIds=CONFLICT_SCHEMAS):
    source = Gio.SettingsSchemaSource.get_default()
    bindings = []
    for schemaId in schemaIds:
        schema = source.lookup(schemaId, True) if source else None
        if schema is None:
            if schemaId not in missingSchemasReported:
                missingSchemasReported.add(schemaId)
                print(f"warning: gsettings schema {schemaId} is not installed, skipped in the conflict check", file=sys.stderr)
            continue
        settings = Gio.Settings.new_full(schema, None, None)
        for key in schema.list_keys():
            value = settings.get_value(key)
            if value.get_type_string() != "as":
                continue
            for accelerator in value.unpack():
                bindings.append((schemaId, key, accelerator))
    return bindings


def matchConflicts(binding, customShortcuts, systemShortcuts, excludeCustomId=None):
    target = normalizeAccelerator(binding)
    if target is None:
        return []
    conflicts = []
    for shortcut in customShortcuts:
        if shortcut.customId == excludeCustomId:
            continue
        if normalizeAccelerator(shortcut.binding) == target:
            conflicts.append(f"custom shortcut \"{shortcut.name}\"")
    for schemaId, key, accelerator in systemShortcuts:
        label = f"system shortcut \"{key}\" ({schemaId})"
        if label not in conflicts and normalizeAccelerator(accelerator) == target:
            conflicts.append(label)
    return conflicts


def findConflicts(binding, excludeCustomId=None):
    if not binding:
        return []
    return matchConflicts(binding, listShortcuts(), systemBindings(), excludeCustomId)


def keyEventToAccelerator(keyval, state):
    keyvalName = Gtk.accelerator_name(keyval, 0)
    if keyvalName in IGNORED_KEYVALS:
        return None
    mask = state & Gtk.accelerator_get_default_mod_mask()
    accel = Gtk.accelerator_name(keyval, mask)
    if not accel or not Gtk.accelerator_valid(keyval, mask):
        return None
    return accel
