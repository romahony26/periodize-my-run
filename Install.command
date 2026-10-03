#!/bin/sh
# Double-click to install Periodize My Run on a Mac. It downloads what the Mac lacks (Python if there is none, and the libraries).
# The first time, macOS may say it cannot check this file: right-click it, choose Open, then Open again.
# Keep this folder where it is: the app runs from here.
cd "$(dirname "$0")" || exit 1
./install.sh && { echo; echo "Opening http://localhost:8321"; sleep 2; open "http://localhost:8321"; }
echo; echo "You can close this window."
