#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
cinnamon-shortcut-manager
==========================

A small GTK3 GUI for managing Cinnamon custom keyboard shortcuts: add, edit,
delete, and see everything currently registered - no manual editing of
Cinnamon Settings -> Keyboard -> Shortcuts -> Custom Shortcuts required.

Shortcuts are written straight to gsettings/dconf (see keybindings.py), the
same storage Cinnamon's own keybinding manager reads from, so anything
created here is live system-wide immediately, survives logout/login, and
shows up in Cinnamon Settings too.

Run directly: python3 shortcut_manager.py
"""

import os
import sys

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keybindings
import presets


class AccelCaptureEntry(Gtk.Entry):
    """A read-only entry that captures the next key combo pressed into it."""

    def __init__(self):
        super().__init__()
        self.set_editable(False)
        self.set_placeholder_text("Click here, then press a key combo")
        self.accelerator = ""
        self.connect("key-press-event", self._onKeyPress)
        self.connect("button-press-event", self._onFocusRequest)

    def _onFocusRequest(self, widget, event):
        self.grab_focus()
        return False

    def _onKeyPress(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.setAccelerator("")
            return True
        if event.keyval == Gdk.KEY_BackSpace and not (event.state & Gtk.accelerator_get_default_mod_mask()):
            self.setAccelerator("")
            return True
        accel = keybindings.keyEventToAccelerator(event.keyval, event.state)
        if accel:
            self.setAccelerator(accel)
        return True

    def setAccelerator(self, accel):
        self.accelerator = accel
        if not accel:
            self.set_text("")
            return
        keyval, mods = Gtk.accelerator_parse(accel)
        self.set_text(Gtk.accelerator_get_label(keyval, mods) if keyval else accel)


class ShortcutDialog(Gtk.Dialog):
    def __init__(self, parent, shortcut=None):
        title = "Edit shortcut" if shortcut else "Add shortcut"
        super().__init__(title=title, transient_for=parent, modal=True)
        self.set_default_size(420, -1)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
        )
        self.editingId = shortcut.customId if shortcut else None

        grid = Gtk.Grid(column_spacing=10, row_spacing=8, margin=12)
        self.get_content_area().add(grid)

        grid.attach(Gtk.Label(label="Name", xalign=0), 0, 0, 1, 1)
        self.nameEntry = Gtk.Entry()
        grid.attach(self.nameEntry, 1, 0, 1, 1)

        grid.attach(Gtk.Label(label="Command", xalign=0), 0, 1, 1, 1)
        self.commandEntry = Gtk.Entry()
        grid.attach(self.commandEntry, 1, 1, 1, 1)

        available = presets.availablePresets()
        if available:
            grid.attach(Gtk.Label(label="Preset", xalign=0), 0, 2, 1, 1)
            presetCombo = Gtk.ComboBoxText()
            presetCombo.append_text("(custom command)")
            for label, _command in available:
                presetCombo.append_text(label)
            presetCombo.set_active(0)
            presetCombo.connect("changed", self._onPresetChanged, available)
            grid.attach(presetCombo, 1, 2, 1, 1)

        grid.attach(Gtk.Label(label="Shortcut", xalign=0), 0, 3, 1, 1)
        self.accelEntry = AccelCaptureEntry()
        grid.attach(self.accelEntry, 1, 3, 1, 1)

        self.warningLabel = Gtk.Label(xalign=0)
        self.warningLabel.set_line_wrap(True)
        self.warningLabel.get_style_context().add_class("warning")
        grid.attach(self.warningLabel, 0, 4, 2, 1)

        if shortcut:
            self.nameEntry.set_text(shortcut.name)
            self.commandEntry.set_text(shortcut.command)
            self.accelEntry.setAccelerator(shortcut.binding)

        self.accelEntry.connect("key-release-event", lambda w, e: self._refreshConflictWarning())
        self.show_all()
        self._refreshConflictWarning()

    def _onPresetChanged(self, combo, available):
        index = combo.get_active()
        if index <= 0:
            return
        label, command = available[index - 1]
        self.commandEntry.set_text(command)
        if not self.nameEntry.get_text():
            self.nameEntry.set_text(label)

    def _refreshConflictWarning(self):
        accel = self.accelEntry.accelerator
        conflicts = keybindings.findConflicts(accel, excludeCustomId=self.editingId) if accel else []
        if conflicts:
            self.warningLabel.set_text("Conflicts with: " + ", ".join(conflicts))
        else:
            self.warningLabel.set_text("")

    def result(self):
        return self.nameEntry.get_text().strip(), self.commandEntry.get_text().strip(), self.accelEntry.accelerator


class ShortcutManagerWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Custom Shortcuts")
        self.set_default_size(640, 420)
        self.set_border_width(8)

        rootBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(rootBox)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        rootBox.pack_start(toolbar, False, False, 0)

        addButton = Gtk.Button(label="Add")
        addButton.connect("clicked", self._onAdd)
        toolbar.pack_start(addButton, False, False, 0)

        self.editButton = Gtk.Button(label="Edit")
        self.editButton.connect("clicked", self._onEdit)
        self.editButton.set_sensitive(False)
        toolbar.pack_start(self.editButton, False, False, 0)

        self.deleteButton = Gtk.Button(label="Delete")
        self.deleteButton.connect("clicked", self._onDelete)
        self.deleteButton.set_sensitive(False)
        toolbar.pack_start(self.deleteButton, False, False, 0)

        refreshButton = Gtk.Button(label="Refresh")
        refreshButton.connect("clicked", lambda w: self._reload())
        toolbar.pack_end(refreshButton, False, False, 0)

        self.store = Gtk.ListStore(str, str, str, str)
        self.treeView = Gtk.TreeView(model=self.store)
        for index, columnTitle in enumerate(["Name", "Shortcut", "Command"]):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(columnTitle, renderer, text=index)
            column.set_resizable(True)
            column.set_expand(index == 2)
            self.treeView.append_column(column)
        self.treeView.get_selection().connect("changed", self._onSelectionChanged)
        self.treeView.connect("row-activated", lambda *_: self._onEdit(None))

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.add(self.treeView)
        rootBox.pack_start(scroller, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        self._reload()

    def _reload(self):
        self.store.clear()
        for shortcut in keybindings.listShortcuts():
            self.store.append([shortcut.name, shortcut.label(), shortcut.command, shortcut.customId])

    def _onSelectionChanged(self, selection):
        hasSelection = selection.get_selected()[1] is not None
        self.editButton.set_sensitive(hasSelection)
        self.deleteButton.set_sensitive(hasSelection)

    def _selectedShortcut(self):
        model, treeIter = self.treeView.get_selection().get_selected()
        if not treeIter:
            return None
        customId = model[treeIter][3]
        return next((s for s in keybindings.listShortcuts() if s.customId == customId), None)

    def _onAdd(self, widget):
        dialog = ShortcutDialog(self)
        if dialog.run() == Gtk.ResponseType.OK:
            name, command, binding = dialog.result()
            if name and command and binding:
                keybindings.addShortcut(name, command, binding)
                self._reload()
        dialog.destroy()

    def _onEdit(self, widget):
        shortcut = self._selectedShortcut()
        if not shortcut:
            return
        dialog = ShortcutDialog(self, shortcut)
        if dialog.run() == Gtk.ResponseType.OK:
            name, command, binding = dialog.result()
            if name and command:
                keybindings.updateShortcut(shortcut.customId, name, command, binding)
                self._reload()
        dialog.destroy()

    def _onDelete(self, widget):
        shortcut = self._selectedShortcut()
        if not shortcut:
            return
        confirm = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO, text=f"Delete shortcut \"{shortcut.name}\"?",
        )
        response = confirm.run()
        confirm.destroy()
        if response == Gtk.ResponseType.YES:
            keybindings.deleteShortcut(shortcut.customId)
            self._reload()


def main():
    window = ShortcutManagerWindow()
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
