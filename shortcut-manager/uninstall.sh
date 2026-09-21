#!/usr/bin/env bash
set -euo pipefail

installDir="$HOME/.local/share/cinnamon-shortcut-manager"
desktopFile="$HOME/.local/share/applications/cinnamon-shortcut-manager.desktop"

rm -rf "$installDir"
rm -f "$desktopFile"

echo "removed shortcut-manager"
echo "shortcuts it created stay active; they belong to Cinnamon (org.cinnamon.desktop.keybindings)"
