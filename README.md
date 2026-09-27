# cinnamon-tweaks

Two small GTK 3 utilities for the Cinnamon desktop that put frequently changed
settings one click away instead of several pages deep in Cinnamon Settings.
`shortcut-manager` lists, adds, edits and deletes custom keyboard shortcuts;
`panel-tweaks` toggles panel auto-hide and edit mode, sets the panel height and
enables or disables applets. Neither tool has storage of its own: both read and
write the same gsettings/dconf keys Cinnamon uses, so every change applies
immediately, survives logout and shows up in Cinnamon Settings. No daemon runs
in the background, and the two tools install independently.

| Tool | Replaces | Interface |
| --- | --- | --- |
| [`shortcut-manager`](#shortcut-manager) | Settings > Keyboard > Shortcuts > Custom Shortcuts | GTK window, menu launcher |
| [`panel-tweaks`](#panel-tweaks) | Settings > Panel | GTK window, menu launcher |

## Requirements

- Cinnamon. Both tools use `org.cinnamon.*` gsettings schemas and do nothing
  useful on other desktops.
- Python 3
- PyGObject with GTK 3
- `dconf` command-line tool (optional, used by `shortcut-manager`; see below)

On Linux Mint and other Debian derivatives:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 dconf-cli
```

## shortcut-manager

A window listing every custom keyboard shortcut, with buttons to add, edit,
delete and refresh.

### Features

- **One table** with the name, key combination and command of every custom
  shortcut listed in Cinnamon's `custom-list`. Double-clicking a row opens it
  for editing.
- **Key capture.** The shortcut field records the next combination you press
  instead of asking you to type `<Super><Shift>t`. Escape, or Backspace without
  modifiers, clears it. Lone modifier keys are ignored and only combinations
  GTK accepts as valid accelerators are recorded.
- **Conflict warnings.** While you edit, the dialog lists every other custom
  shortcut and every built-in binding that already uses the same combination.
  Built-in bindings are read from `org.cinnamon.desktop.keybindings`,
  `org.cinnamon.desktop.keybindings.wm`,
  `org.cinnamon.desktop.keybindings.media-keys`,
  `org.cinnamon.muffin.keybindings` and `org.gnome.desktop.wm.keybindings`;
  a schema that is not installed is skipped with a warning on stderr.
  Combinations are compared after normalization, so modifier order, the
  spellings `<Control>`, `<Ctrl>` and `<Primary>`, and the case of the key
  name do not hide a conflict. A conflict is a warning, not a block: you can
  still save.
- **Command presets.** The dialog offers quick-fill commands, each shown only
  when its program is installed:

  | Preset | Command |
  | --- | --- |
  | Terminal | `gnome-terminal` |
  | File manager | `nemo` |
  | Lock screen | `cinnamon-screensaver-command --lock` |
  | Screenshot - area | `flameshot gui` |
  | Screenshot - full screen | `gnome-screenshot` |
  | Web browser | `xdg-open http://` |
  | Mute volume toggle | `amixer -q set Master toggle` |
  | Text editor | `gedit` |

  Picking a preset fills the command, and the name if it is still empty.
- **Clean slot handling.** A new shortcut takes the lowest free `customN` id,
  also skipping ids that other tools left behind in dconf. Deleting a shortcut
  removes it from `custom-list` and resets its whole dconf path, so nothing is
  left orphaned. Both of these use the `dconf` tool; without it, ids are picked
  from `custom-list` only and deleted entries keep their values in dconf.
- **Delete confirmation** before anything is removed.

A new shortcut is saved only when it has a name, a command and a key
combination. An edit needs a name and a command; clearing the combination
leaves the shortcut unbound.

### Where the settings live

Each custom shortcut lives at
`/org/cinnamon/desktop/keybindings/custom-keybindings/customN/` (schema
`org.cinnamon.desktop.keybindings.custom-keybinding`) with `name`, `command`
and `binding` keys. The list of active ids is `custom-list` in
`org.cinnamon.desktop.keybindings`. Shortcuts created here are identical to
ones made in Cinnamon Settings.

## panel-tweaks

A window with the panel settings worth a one-click toggle.

### Features

- **Auto-hide** on or off.
- **Edit mode** on or off (the mode in which applets can be dragged around the
  panel).
- **Panel height** slider from 20 to 80 pixels, applied live while dragging.
  A panel without a stored height is shown as 40.
- **Applet list** for the panel, showing each applet's id and zone with a
  checkbox to enable or disable it.

### Where the settings live

All in the `org.cinnamon` schema: `panels-enabled`, `panels-autohide`,
`panels-height`, `panel-edit-mode` and `enabled-applets`.

## Install and run

Each tool has its own `install.sh` and `uninstall.sh`. Installing copies the
tool into `~/.local/share/` and adds a launcher to the applications menu under
Settings:

```bash
./shortcut-manager/install.sh    # ~/.local/share/cinnamon-shortcut-manager, "Custom Shortcuts"
./panel-tweaks/install.sh        # ~/.local/share/cinnamon-panel-tweaks, "Panel Tweaks"
```

Uninstalling removes the copied files and the launcher. Shortcuts and panel
settings changed through the tools stay in effect, because they belong to
Cinnamon:

```bash
./shortcut-manager/uninstall.sh
./panel-tweaks/uninstall.sh
```

Both tools also run straight from a checkout without installing:

```bash
python3 shortcut-manager/shortcut_manager.py
python3 panel-tweaks/panel_tweaks.py
```

There is nothing to build.

## Tests

Each tool has unit tests for its non-GUI logic, written with the standard
library `unittest` module, so they need nothing beyond the runtime
requirements. Run them from the repository root:

```bash
python3 -m unittest discover -s shortcut-manager/tests -t shortcut-manager
python3 -m unittest discover -s panel-tweaks/tests -t panel-tweaks
```

- `shortcut-manager`: accelerator normalization, conflict matching against
  custom and built-in shortcuts, reading built-in bindings from gsettings and
  skipping a missing schema. The gsettings tests compile a throwaway schema
  with `glib-compile-schemas` and use the in-memory gsettings backend, so they
  never touch your real settings; they are skipped if `glib-compile-schemas`
  is not installed.
- `panel-tweaks`: reading and writing the per-panel `id:value` lists and
  picking the managed panel, against a fake settings object.

The GTK windows themselves are checked by hand on a Cinnamon desktop. Static
checks:

```bash
python3 -m py_compile shortcut-manager/*.py panel-tweaks/*.py
bash -n shortcut-manager/*.sh panel-tweaks/*.sh
```

## Project layout

```
shortcut-manager/
  shortcut_manager.py   GTK window, add/edit dialog, key capture entry
  keybindings.py        reading and writing custom shortcuts, conflict lookup
  presets.py            command presets, filtered by installed programs
  tests/                unit tests
  install.sh
  uninstall.sh
panel-tweaks/
  panel_tweaks.py       GTK window and the panel gsettings helpers
  tests/                unit tests
  install.sh
  uninstall.sh
```

## Limitations

- Cinnamon only. Built-in schemas missing from the conflict check are skipped,
  but the custom shortcut schemas themselves must be installed.
- The shortcut table does not refresh by itself when shortcuts are changed
  elsewhere; use Refresh.
- `panel-tweaks` manages one panel: the first id listed in `panels-enabled`.
  Other panels are ignored. Edit mode is a global Cinnamon setting and affects
  all panels.
- Disabling an applet removes it from `enabled-applets` immediately. It can be
  re-enabled while the window is open, but after reopening the tool it is no
  longer listed and has to be added back through Cinnamon Settings.
- Neither tool is a layout editor or applet manager; that stays with Cinnamon
  Settings.
- Tested on Linux Mint 22.2 with Cinnamon on X11.

## License

MIT. See [LICENSE](LICENSE).
