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

## Local Setup

Python venv in `.venv/`. Install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate  # on Mac
pip install -r requirements.txt
```

Run locally: `python web.py` (or check `install.sh` for the exact command).

## Testing Before Commit

1. Start the app locally: `python web.py`
2. Open http://localhost:5000 in a browser
3. Test your change end-to-end (golden path + edge cases)
4. Check for regressions in unrelated features
5. Stop the app and commit

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

**Why:** The app's update checker looks for GitHub releases. Without tags, new versions don't appear in the update feature.

## Deployment

**Mac:** App restarts automatically when updated via the built-in updater.

**Pi:** Known issue — venv setup sometimes fails on Pi. If SSH deployment breaks, it's likely a Python environment issue on the Pi side, not the code.

## Permissions

File editing, git, bash, and read permissions are enabled. Use them freely.
