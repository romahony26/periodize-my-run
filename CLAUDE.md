# Periodize My Run — Claude Guidelines

## Releases & Tagging

**Always create and push a git tag after committing changes.**

After each commit, extract the version from `CHANGELOG.md` and create a tag:

```bash
git tag v{version}
git push origin v{version}
```

**Why:** The app's update checker looks for GitHub releases/tags. Without tags, new versions don't appear in the update feature.

**Example:** If CHANGELOG shows `2.9.1-beta.7`, run:
```bash
git tag v2.9.1-beta.7
git push origin v2.9.1-beta.7
```

## CHANGELOG

Every code change needs a versioned entry in `CHANGELOG.md` with:
- Version and date (YYYY-MM-DD)
- Section: Added, Changed, Removed, or Fixed
- Clear one-line descriptions

## Permissions

File editing, git, bash, and read permissions are enabled by default.

## Git Branches

- `main` — stable releases only
- `beta` — development, tagged as `-beta.N`
