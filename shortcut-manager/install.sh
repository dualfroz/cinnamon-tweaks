#!/usr/bin/env bash
# Installs cinnamon-shortcut-manager for the current user:
#   - copies the app into ~/.local/share/cinnamon-shortcut-manager/
#   - creates a menu launcher (~/.local/share/applications/)
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/cinnamon-shortcut-manager"
DESKTOP_FILE="$HOME/.local/share/applications/cinnamon-shortcut-manager.desktop"

mkdir -p "$APP_DIR" "$(dirname "$DESKTOP_FILE")"
cp "$SRC_DIR/shortcut_manager.py" "$SRC_DIR/keybindings.py" "$SRC_DIR/presets.py" "$APP_DIR/"
chmod +x "$APP_DIR/shortcut_manager.py"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Custom Shortcuts
Comment=Add, edit and delete custom Cinnamon keyboard shortcuts
Exec=python3 $APP_DIR/shortcut_manager.py
Icon=preferences-desktop-keyboard-shortcuts
Terminal=false
Categories=Settings;
EOF

echo "Installed -> $APP_DIR"
echo "Menu launcher -> $DESKTOP_FILE"
echo "Run directly with: python3 $APP_DIR/shortcut_manager.py"
