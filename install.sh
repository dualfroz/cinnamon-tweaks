#!/usr/bin/env bash
# Installs cinnamon-panel-tweaks for the current user:
#   - copies the app into ~/.local/share/cinnamon-panel-tweaks/
#   - creates a menu launcher (~/.local/share/applications/)
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/cinnamon-panel-tweaks"
DESKTOP_FILE="$HOME/.local/share/applications/cinnamon-panel-tweaks.desktop"

mkdir -p "$APP_DIR" "$(dirname "$DESKTOP_FILE")"
cp "$SRC_DIR/panel_tweaks.py" "$APP_DIR/"
chmod +x "$APP_DIR/panel_tweaks.py"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Panel Tweaks
Comment=Quick toggles for the Cinnamon panel: autohide, height, edit mode, applets
Exec=python3 $APP_DIR/panel_tweaks.py
Icon=preferences-desktop-cinnamon
Terminal=false
Categories=Settings;
EOF

echo "Installed -> $APP_DIR"
echo "Menu launcher -> $DESKTOP_FILE"
echo "Run directly with: python3 $APP_DIR/panel_tweaks.py"
