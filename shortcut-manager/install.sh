#!/usr/bin/env bash
set -euo pipefail

sourceDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
installDir="$HOME/.local/share/cinnamon-shortcut-manager"
desktopFile="$HOME/.local/share/applications/cinnamon-shortcut-manager.desktop"

mkdir -p "$installDir" "$(dirname "$desktopFile")"
cp "$sourceDir/shortcut_manager.py" "$sourceDir/keybindings.py" "$sourceDir/presets.py" "$installDir/"
chmod +x "$installDir/shortcut_manager.py"

cat > "$desktopFile" <<EOF
[Desktop Entry]
Type=Application
Name=Custom Shortcuts
Comment=Add, edit and delete custom Cinnamon keyboard shortcuts
Exec=python3 "$installDir/shortcut_manager.py"
Icon=preferences-desktop-keyboard-shortcuts
Terminal=false
Categories=Settings;
EOF

echo "installed shortcut-manager into $installDir"
echo "menu launcher: $desktopFile"
echo "run directly: python3 $installDir/shortcut_manager.py"
