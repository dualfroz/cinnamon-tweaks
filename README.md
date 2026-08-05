# cinnamon-tweaks

Two small GTK 3 desktop utilities for the Cinnamon desktop environment, each
one built around the same frustration: a setting you change often enough to
resent how many clicks it takes to reach through Cinnamon Settings.

| Tool | Replaces | Interface |
| --- | --- | --- |
| [`shortcut-manager`](#shortcut-manager) | Settings → Keyboard → Shortcuts → Custom Shortcuts | GTK window, menu launcher |
| [`panel-tweaks`](#panel-tweaks) | Settings → Panel | GTK window, menu launcher |

Neither tool invents its own storage. Both read and write exactly the same
gsettings/dconf keys Cinnamon itself uses, so every change is live immediately,
survives logout, and shows up in Cinnamon Settings as if you had made it there.
Nothing needs to be restarted and no daemon runs in the background.

They install independently — take one, both, or neither.

## Requirements

- Cinnamon (the tools read `org.cinnamon.*` gsettings schemas, so they will not
  do anything useful on GNOME, KDE or anything else)
- Python 3
- PyGObject with GTK 3
- `dconf` command-line tool — used by `shortcut-manager` to discover orphaned
  shortcut slots and to delete shortcuts cleanly. Optional; the tool degrades
  gracefully if it is missing.

On Linux Mint and other Debian derivatives:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 dconf-cli
```

---

## shortcut-manager

A window that lists every custom keyboard shortcut registered on your desktop
and lets you add, edit and delete them.

### Features

- **One list of everything.** Name, key combo and command for every custom
  shortcut, in one sortable table.
- **Capture instead of type.** The shortcut field records the next combination
  you press rather than asking you to spell out `<Super><Shift>T`. Escape or
  Backspace clears it.
- **Conflict warnings.** Before you save, the dialog tells you if the
  combination is already taken — by another custom shortcut, or by a built-in
  one. It checks the Cinnamon desktop, window manager, media-key, Muffin and
  GNOME window-manager schemas.
- **Command presets.** The new-shortcut dialog offers quick-fill commands for
  a terminal, file manager, screen lock, screenshot tools, volume mute, browser
  and text editor. Only presets whose binary is actually installed are offered,
  so the list never suggests a command that would fail.
- **No orphans.** New shortcuts claim the lowest free `customN` slot, taking
  into account slots left behind in dconf by other tools, and deleting a
  shortcut resets its dconf path rather than just unlisting it.

### Installing

```bash
cd shortcut-manager
./install.sh
```

Copies the app into `~/.local/share/cinnamon-shortcut-manager` and adds a
"Custom Shortcuts" launcher to your applications menu under Settings.

To run it without installing:

```bash
python3 shortcut-manager/shortcut_manager.py
```

### Where the settings live

Cinnamon stores custom shortcuts as a relocatable schema. Each one lives at
`/org/cinnamon/desktop/keybindings/custom-keybindings/customN/` with `name`,
`command` and `binding` keys, and the list of active ids sits in `custom-list`
under `org.cinnamon.desktop.keybindings`. This tool writes precisely those, so
anything it creates is indistinguishable from a shortcut made by hand.

---

## panel-tweaks

A window with the handful of panel settings worth a one-click toggle.

### Features

- **Auto-hide** the panel on or off.
- **Edit mode** on or off — the mode that lets you drag applets around the
  panel.
- **Panel height** on a slider, from 20 to 80 pixels, applied live as you drag.
- **Applet list** for the panel, with a checkbox to enable or disable each one.

### Installing

```bash
cd panel-tweaks
./install.sh
```

Copies the app into `~/.local/share/cinnamon-panel-tweaks` and adds a "Panel
Tweaks" launcher to your applications menu under Settings.

To run it without installing:

```bash
python3 panel-tweaks/panel_tweaks.py
```

### Limitations worth knowing

- **It only manages one panel.** If you have several panels configured, the tool
  operates on the first one listed in `panels-enabled` and ignores the rest.
- **Disabling an applet is one-way within a session.** Unchecking an applet
  removes it from `enabled-applets` immediately. You can re-check the box while
  the window is still open, but once you close and reopen the tool the applet is
  no longer in the list, and you will need Cinnamon Settings to bring it back.
- It deliberately does not try to be a layout editor or an applet manager.
  That is Cinnamon Settings' job; this is a shortcut to the knobs used often.

### Where the settings live

All under the `org.cinnamon` schema: `panels-enabled`, `panels-autohide`,
`panels-height`, `panel-edit-mode` and `enabled-applets`.

---

## Tested on

Linux Mint 22.2 with Cinnamon, on an X11 session. Both tools depend on Cinnamon
schemas specifically and are not expected to work on other desktops.

## Licence

No licence has been chosen yet.
