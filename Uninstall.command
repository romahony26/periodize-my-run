#!/bin/sh
# Double-click to stop Periodize My Run and stop it starting at login. Your data is kept.
# To delete your data too, run  ./uninstall.sh --data  in Terminal.
cd "$(dirname "$0")" || exit 1
./uninstall.sh
echo; echo "You can close this window, then delete this folder."
