#!/bin/sh
# Runs the uninstall that was approved inside the app (Settings, Remove Periodize My Run). The installer registers it with the system
# (a launchd agent on macOS, a systemd path unit on Linux) so that it starts when the app drops a request file, and for no other reason.
#
#   uninstall-run.sh APP_DIR DATA_DIR KEY_DIR [USER]
#
# The arguments are fixed by the installer; nothing the app writes is ever run or used as a path. The app can only create one file,
# DATA_DIR/uninstall-request, and the only things this script takes from it are whether its first line is exactly "keep" or "data".
# On Linux a copy of this script is installed owned by root where the app's user cannot change it, because it runs as root there.
set -u
DIR="$1"; DATA="$2"; KEYS="$3"; USER_NAME="${4:-}"
FLAG="$DATA/uninstall-request"

[ ! -L "$DATA" ] && [ -f "$FLAG" ] && [ ! -L "$FLAG" ] || exit 0
MODE="$(head -c 8 "$FLAG" | head -n 1)"
rm -f "$FLAG"
case "$MODE" in keep|data) ;; *) exit 0 ;; esac
sleep 3         # let the app finish answering the browser

# Run as the app's own user, so a swapped-in link cannot make a root process delete something else.
as_user() { if [ -n "$USER_NAME" ] && [ "$(id -u)" = 0 ]; then runuser -u "$USER_NAME" -- "$@"; else "$@"; fi; }
safe_rm() { for p in "$@"; do [ -e "$p" ] && [ ! -L "$p" ] && as_user rm -rf -- "$p"; done; return 0; }

if [ "$(uname)" = "Darwin" ]; then
  APP="$HOME/Library/LaunchAgents/com.periodizemyrun.app.plist"
  WATCH="$HOME/Library/LaunchAgents/com.periodizemyrun.uninstall.plist"
  launchctl unload "$APP" 2>/dev/null; rm -f "$APP"
  rm -f "$WATCH"
  safe_rm "$DIR/.venv" "$DIR/.python"
  [ "$MODE" = data ] && safe_rm "$DATA" "$KEYS"
  launchctl unload "$WATCH" 2>/dev/null          # last: this job is the one running
else
  systemctl disable --now periodize-my-run.service
  rm -f /etc/systemd/system/periodize-my-run.service
  safe_rm "$DIR/.venv" "$DIR/.python"
  [ "$MODE" = data ] && safe_rm "$DATA" "$KEYS"
  rm -f /etc/systemd/system/periodize-my-run-uninstall.service /usr/local/libexec/periodize-my-run-uninstall
  systemctl disable --now periodize-my-run-uninstall.path 2>/dev/null
  rm -f /etc/systemd/system/periodize-my-run-uninstall.path
  systemctl daemon-reload
fi
exit 0
