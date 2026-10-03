#!/bin/sh
# Periodize installer for macOS and Raspberry Pi OS / DietPi (Debian).
# Creates a Python environment, then registers the app to start at boot and stay running.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PYTHON:-python3}"
PORT="${PERIODIZE_PORT:-8321}"

"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' || { echo "Python 3.12 or later is needed (found $($PY --version))."; exit 1; }
echo "Creating Python environment..."
"$PY" -m venv "$DIR/.venv"
"$DIR/.venv/bin/pip" install --quiet --upgrade pip
"$DIR/.venv/bin/pip" install --quiet --require-hashes -r "$DIR/requirements.lock"   # exact versions, each checked against its published SHA-256

if [ "$(uname)" = "Darwin" ]; then
  HOST="${PERIODIZE_HOST:-127.0.0.1}"
  PLIST="$HOME/Library/LaunchAgents/com.periodize.app.plist"
  mkdir -p "$HOME/Library/LaunchAgents" "$HOME/.periodize/logs"
  cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.periodize.app</string>
  <key>ProgramArguments</key><array><string>$DIR/.venv/bin/python</string><string>$DIR/web.py</string><string>--host</string><string>$HOST</string><string>--port</string><string>$PORT</string></array>
  <key>RunAtLoad</key><true/><key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$HOME/.periodize/logs/service.out</string>
  <key>StandardErrorPath</key><string>$HOME/.periodize/logs/service.err</string>
</dict></plist>
PL
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "Periodize is running. Open http://localhost:$PORT"
else
  HOST="${PERIODIZE_HOST:-0.0.0.0}"
  # The app is reachable from other devices, so it needs a password and an encrypted connection before it starts.
  "$DIR/.venv/bin/python" "$DIR/web.py" --set-password
  mkdir -p "$HOME/.periodize" "$HOME/.config/periodize" && chmod 700 "$HOME/.periodize" "$HOME/.config/periodize"
  TLS="$HOME/.periodize/tls"
  if [ ! -f "$TLS/cert.pem" ] && command -v openssl >/dev/null 2>&1; then
    mkdir -p "$TLS" && chmod 700 "$TLS"
    IPADDR="$(hostname -I 2>/dev/null | awk '{print $1}')"
    openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -keyout "$TLS/key.pem" -out "$TLS/cert.pem" \
      -subj "/CN=$(hostname)" -addext "subjectAltName=DNS:$(hostname),DNS:$(hostname).local${IPADDR:+,IP:$IPADDR}" >/dev/null 2>&1
    chmod 600 "$TLS/key.pem"
    echo "Created a self-signed certificate. Your browser will warn once; that is expected."
  fi
  UNIT=/etc/systemd/system/periodize.service
  sudo tee "$UNIT" >/dev/null <<UN
[Unit]
Description=Periodize training planner
After=network-online.target
Wants=network-online.target

[Service]
User=$(id -un)
WorkingDirectory=$DIR
ExecStart=$DIR/.venv/bin/python $DIR/web.py --host $HOST --port $PORT
Restart=always
RestartSec=10
# The service can write only to its own data folders, gains no privileges, and sees a private /tmp.
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$HOME/.periodize $HOME/.config/periodize
ProtectKernelTunables=true
ProtectKernelModules=true
ProtectControlGroups=true
RestrictSUIDSGID=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
LockPersonality=true
CapabilityBoundingSet=
UMask=0077

[Install]
WantedBy=multi-user.target
UN
  sudo systemctl daemon-reload
  sudo systemctl enable --now periodize.service
  IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
  SCHEME=http; [ -f "$HOME/.periodize/tls/cert.pem" ] && SCHEME=https
  echo "Periodize is running. Open $SCHEME://${IP:-<this device>}:$PORT from any device on your network and log in with the app password."
fi
