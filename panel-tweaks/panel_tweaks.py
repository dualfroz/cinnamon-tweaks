#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cinnamon-panel-tweaks
=======================

A small GTK3 GUI for the handful of Cinnamon bottom-panel settings that
otherwise require digging through Cinnamon Settings -> Panel: autohide,
height, edit mode (drag applets around), and per-applet enable/disable.
Everything here reads and writes the same "org.cinnamon" gsettings keys
Cinnamon Settings itself uses, so changes apply live, no restart needed.

This intentionally does not attempt applet development or layout editing
beyond enable/disable + reorder-via-edit-mode - that is Cinnamon Settings'
job. This is a quick-access shortcut to the few knobs used often enough to
be worth a one-click toggle.

Run directly: python3 panel_tweaks.py
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio

CINNAMON_SCHEMA = "org.cinnamon"

DEFAULT_PANEL_ID = "1"


def _panelsEnabledIds(settings):
    ids = []
    for entry in settings.get_strv("panels-enabled"):
        panelId = entry.split(":", 1)[0]
        if panelId not in ids:
            ids.append(panelId)
    return ids or [DEFAULT_PANEL_ID]


def _readPanelIndexedValue(settings, key, panelId, fallback):
    for entry in settings.get_strv(key):
        prefix, _, value = entry.partition(":")
        if prefix == panelId:
            return value
    return fallback


def _writePanelIndexedValue(settings, key, panelId, value):
    entries = settings.get_strv(key)
    updated = []
    found = False
    for entry in entries:
        prefix, _, _oldValue = entry.partition(":")
        if prefix == panelId:
            updated.append(f"{panelId}:{value}")
            found = True
        else:
            updated.append(entry)
    if not found:
        updated.append(f"{panelId}:{value}")
    settings.set_strv(key, updated)


class AppletRow(Gtk.Box):
    def __init__(self, panelId, zone, position, appletId, instanceId, onToggle):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.panelId = panelId
        self.zone = zone
        self.position = position
        self.appletId = appletId
        self.instanceId = instanceId

        check = Gtk.CheckButton()
        check.set_active(True)
        check.connect("toggled", onToggle, self)
        self.pack_start(check, False, False, 0)
        self.pack_start(Gtk.Label(label=f"{appletId}  ({zone})", xalign=0), True, True, 0)


class PanelTweaksWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Panel Tweaks")
        self.set_default_size(460, 420)
        self.set_border_width(10)
        self.settings = Gio.Settings.new(CINNAMON_SCHEMA)
        self.panelId = _panelsEnabledIds(self.settings)[0]

        rootBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(rootBox)

        self.autohideSwitch = self._buildSwitchRow(
            rootBox, "Auto-hide panel", self._readAutohide(), self._onAutohideToggled,
        )
        self.editModeSwitch = self._buildSwitchRow(
            rootBox, "Edit mode (drag applets)", self.settings.get_boolean("panel-edit-mode"),
            self._onEditModeToggled,
        )

        heightBox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        heightBox.pack_start(Gtk.Label(label="Panel height"), False, False, 0)
        adjustment = Gtk.Adjustment(value=self._readHeight(), lower=20, upper=80, step_increment=1)
        self.heightScale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        self.heightScale.set_digits(0)
        self.heightScale.set_hexpand(True)
        self.heightScale.connect("value-changed", self._onHeightChanged)
        heightBox.pack_start(self.heightScale, True, True, 0)
        rootBox.pack_start(heightBox, False, False, 0)

        rootBox.pack_start(Gtk.Separator(), False, False, 4)
        rootBox.pack_start(Gtk.Label(label="Applets on this panel", xalign=0), False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.appletsList = Gtk.ListBox()
        scroller.add(self.appletsList)
        rootBox.pack_start(scroller, True, True, 0)

        self._reloadApplets()
        self.connect("destroy", Gtk.main_quit)

    def _buildSwitchRow(self, rootBox, label, initialState, onToggled):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.pack_start(Gtk.Label(label=label, xalign=0), True, True, 0)
        switch = Gtk.Switch()
        switch.set_active(initialState)
        switch.connect("notify::active", onToggled)
        row.pack_start(switch, False, False, 0)
        rootBox.pack_start(row, False, False, 0)
        return switch

    def _readAutohide(self):
        value = _readPanelIndexedValue(self.settings, "panels-autohide", self.panelId, "false")
        return value == "true"

    def _readHeight(self):
        value = _readPanelIndexedValue(self.settings, "panels-height", self.panelId, "40")
        try:
            return int(value)
        except ValueError:
            return 40

    def _onAutohideToggled(self, switch, _param):
        _writePanelIndexedValue(
            self.settings, "panels-autohide", self.panelId,
            "true" if switch.get_active() else "false",
        )

    def _onEditModeToggled(self, switch, _param):
        self.settings.set_boolean("panel-edit-mode", switch.get_active())

    def _onHeightChanged(self, scale):
        _writePanelIndexedValue(self.settings, "panels-height", self.panelId, str(int(scale.get_value())))

    def _reloadApplets(self):
        for child in self.appletsList.get_children():
            self.appletsList.remove(child)
        self.enabledApplets = self.settings.get_strv("enabled-applets")
        for entry in self.enabledApplets:
            parts = entry.split(":")
            if len(parts) < 5 or parts[0] != f"panel{self.panelId}":
                continue
            _panel, zone, position, appletId, instanceId = parts[0], parts[1], parts[2], parts[3], parts[4]
            row = AppletRow(self.panelId, zone, position, appletId, instanceId, self._onAppletToggled)
            self.appletsList.add(row)
        self.appletsList.show_all()

    def _onAppletToggled(self, check, row):
        entries = list(self.settings.get_strv("enabled-applets"))
        entry = f"panel{row.panelId}:{row.zone}:{row.position}:{row.appletId}:{row.instanceId}"
        if check.get_active():
            if entry not in entries:
                entries.append(entry)
        else:
            entries = [e for e in entries if e != entry]
        self.settings.set_strv("enabled-applets", entries)


def main():
    window = PanelTweaksWindow()
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
