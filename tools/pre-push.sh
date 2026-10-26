#!/bin/sh
# Git pre-push hook (install with tools/install_hooks.sh).
#   push to main (production)  -> the full check, about 6 minutes; the push is refused if it fails
#   push to any other branch   -> the few-second beta check
#   a tag on its own           -> nothing
full=0; beta=0
while read -r local_ref local_sha remote_ref remote_sha; do
  case "$remote_ref" in
    refs/heads/main) full=1 ;;
    refs/heads/*) beta=1 ;;
  esac
done
cd "$(git rev-parse --show-toplevel)" || exit 1
if [ "$full" = 1 ]; then
  echo "Pushing to main (production): running the full check."
  ./check.sh || { echo "Push refused: the full check failed."; exit 1; }
elif [ "$beta" = 1 ]; then
  echo "Pushing a beta: running the fast check."
  ./check.sh beta || { echo "Push refused: the beta check failed."; exit 1; }
fi
exit 0
