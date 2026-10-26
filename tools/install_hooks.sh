#!/bin/sh
# Installs the pre-push hook into this clone (hooks are not part of a commit, so run this once per clone).
cd "$(dirname "$0")/.." || exit 1
cp tools/pre-push.sh "$(git rev-parse --git-path hooks)/pre-push" && chmod +x "$(git rev-parse --git-path hooks)/pre-push" && echo "pre-push hook installed"
