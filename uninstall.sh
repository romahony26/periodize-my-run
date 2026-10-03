#!/bin/sh
# Periodize My Run uninstaller for macOS and Linux (including Raspberry Pi).
#
#   ./uninstall.sh          stop the app, stop it starting by itself, and remove its Python environment. Your data is kept.
#   ./uninstall.sh --data   the same, and also delete your data, backups and the key to your stored Garmin login.
#
# It removes only what the installer made. The app's own folder (this one) is left for you to delete.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
DATA="${PERIODIZE_HOME:-$HOME/.periodize-my-run}"
KEYS="$HOME/.config/periodize-my-run"
WIPE=no
case "${1:-}" in
  --data) WIPE=yes ;;
  "") ;;
  *) echo "Usage: ./uninstall.sh [--data]"; exit 1 ;;
esac

if [ "$(uname)" = "Darwin" ]; then
  PLIST="$HOME/Library/LaunchAgents/com.periodizemyrun.app.plist"
  if [ -f "$PLIST" ]; then
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo "Stopped the app and removed it from login."
  else
    echo "The app was not set to start at login."
  fi
else
  UNIT=/etc/systemd/system/periodize-my-run.service
  if [ -f "$UNIT" ]; then
    sudo systemctl disable --now periodize-my-run.service || true
    sudo rm -f "$UNIT"
    sudo systemctl daemon-reload
    echo "Stopped the app and removed it from start-up."
  else
    echo "The app was not set to start at boot."
  fi
fi

if [ -d "$DIR/.venv" ] || [ -d "$DIR/.python" ]; then
  rm -rf "$DIR/.venv" "$DIR/.python"
  echo "Removed the Python environment."
fi

if [ "$WIPE" = yes ]; then
  echo "This deletes your training data, backups and stored Garmin login for good:"
  echo "  $DATA"
  echo "  $KEYS"
  printf "Type delete to go ahead: "
  read -r answer
  if [ "$answer" = "delete" ]; then
    rm -rf "$DATA" "$KEYS"
    echo "Your data is deleted."
  else
    echo "Nothing was deleted. Your data is still in $DATA"
  fi
else
  echo "Your data is kept in $DATA (run ./uninstall.sh --data to delete it too)."
fi
echo "To finish, delete this folder: $DIR"
