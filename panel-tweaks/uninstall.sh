#!/usr/bin/env bash
set -euo pipefail

installDir="$HOME/.local/share/cinnamon-panel-tweaks"
desktopFile="$HOME/.local/share/applications/cinnamon-panel-tweaks.desktop"

rm -rf "$installDir"
rm -f "$desktopFile"

echo "removed panel-tweaks"
echo "panel settings it changed stay in effect; they belong to Cinnamon (org.cinnamon)"
