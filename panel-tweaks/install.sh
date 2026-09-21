#!/usr/bin/env bash
set -euo pipefail

sourceDir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
installDir="$HOME/.local/share/cinnamon-panel-tweaks"
desktopFile="$HOME/.local/share/applications/cinnamon-panel-tweaks.desktop"

mkdir -p "$installDir" "$(dirname "$desktopFile")"
cp "$sourceDir/panel_tweaks.py" "$installDir/"
chmod +x "$installDir/panel_tweaks.py"

cat > "$desktopFile" <<EOF
[Desktop Entry]
Type=Application
Name=Panel Tweaks
Comment=Quick toggles for the Cinnamon panel: autohide, height, edit mode, applets
Exec=python3 "$installDir/panel_tweaks.py"
Icon=preferences-desktop-cinnamon
Terminal=false
Categories=Settings;
EOF

echo "installed panel-tweaks into $installDir"
echo "menu launcher: $desktopFile"
echo "run directly: python3 $installDir/panel_tweaks.py"
