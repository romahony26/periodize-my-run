# Periodize My Run — Claude Guidelines

## Design Principles

**No persistent input.** Build automatic improvements from data (Garmin, watch sync). Avoid features that need regular user input or new external services.

**Peer-reviewed basis.** Decisions about training (volume limits, pacing, recovery) cite peer-reviewed work, not recent averages or heuristics.

**Mac and Pi.** App runs on user's Mac and optionally on a Raspberry Pi (DietPi) at 192.168.1.2 for always-on syncing. Test both if changes affect sync or background jobs.

## Repository

**What goes in:** Runtime files only (Python, JavaScript, HTML, CSS). Tests are ignored in git.

**Branches:**
- `main` — stable releases only
- `beta` — development, tagged as `-beta.N`

## CHANGELOG & Releases

Every commit needs a versioned entry in `CHANGELOG.md`:
- Version and date (YYYY-MM-DD)
- Section: Added, Changed, Removed, or Fixed
- Clear one-line descriptions

**After commit:** Always create and push a git tag matching the version in CHANGELOG:
```bash
git tag v2.9.1-beta.7
git push origin v2.9.1-beta.7
```

**Why:** The app's update checker reads GitHub tags. Without a tag, a new version does not appear in the update feature.

## Deployment

The Pi does not run `/opt/periodize-my-run` directly: it runs the version folder named in `~/.periodize-my-run/versions/current` (the updater's layout).

Deploy with `python tools/deploy.py` (it uses the version at the top of CHANGELOG.md). It checks that the tag is at HEAD and the tree is clean,
runs ruff and the quick tests, unpacks the tag into `versions/<version>`, backs up the database, switches `current`, restarts the service,
and smoke-tests it (active, `/api/state` reports this version with the keys the page needs, the page and script are served, no traceback in
the journal). If any smoke test fails it puts the previous version back and says so. `--dry-run` shows what it would do.

Before tagging, run `./check.sh` (it runs every stage, including the browser tests and pip-audit). The tests are not in git; `deploy.py`
archives them to `../test-archive/`.
