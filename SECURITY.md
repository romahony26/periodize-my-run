# Security

Periodize holds health data and tokens for your Garmin account. This page says what it protects, what it does not, and how to report a problem.

## What it is designed for

One athlete, on a computer they control (a Mac or a Raspberry Pi), reached from that computer or from their own devices over a home network or a private network such as Tailscale. It is **not** designed to be exposed to the internet.

## What it protects

| Risk | Protection |
| --- | --- |
| Someone on your network opens the app | App password (PBKDF2-SHA256, 600,000 rounds), lockout after 5 failures, session cookie that is HttpOnly, SameSite=Strict and HTTPS-only where HTTPS is used |
| A proxy on the same computer relays strangers | Relayed requests must log in; `--always-login on` makes the computer itself log in too |
| A web page you visit attacks the app in your browser | Writes need a custom header and a matching Origin; unknown host names are refused (DNS rebinding); strict Content-Security-Policy with no inline script |
| Tokens stolen from the database or a backup | Garmin tokens, the cookie-signing key and the notification address are encrypted (Fernet); the key file is separate from the database; backups and exports leave secrets out |
| Passwords | Your Garmin password is used once to sign in and never stored or logged |
| Hostile input | Every setting is type- and range-checked; SQL is parameterised; all page output is escaped; every route is fuzzed on each check run |
| The app being made to call inward | The notification address is refused if it resolves to this computer, link-local or metadata addresses; redirects are not followed |
| Tampered dependencies | Exact versions with SHA-256 checksums (`requirements.lock`); `pip-audit` on every check run |
| Secrets in the code or logs | gitleaks and trufflehog on every check run; logs are scrubbed and owner-only |
| A compromised service on the Pi | The systemd unit runs unprivileged, with a read-only system and write access to its own data folders only |

## What it does not protect against

- **Other people or programs on the same computer.** By default a request from the computer itself needs no password, and anyone who can read your user's files can read the database and the key. Use `--always-login on` on a shared machine, and full-disk encryption.
- **Exposure to the internet.** There is no rate limiting beyond the login lockout, no multi-factor login, and no audit by a third party.
- **Garmin's side.** Garmin access uses an unofficial library; if Garmin changes or blocks it, syncing stops.
- **A lost key file.** `~/.config/periodize/vault.key` is not in backups. Without it the stored tokens cannot be read and you sign in to Garmin again.
- **A changing address between check and use.** The notification address is checked when saved and again when used; a name that changes where it points in between is a small remaining risk.

## Checks

`./check.sh` runs: ruff, bandit, pip-audit, the security and OWASP Top 10 attack tests, the fuzz tests, the feature tests, the browser and accessibility tests, gitleaks and trufflehog. A release should pass all of them.

## Reporting a problem

Please report privately, not in a public issue: use the repository's private security advisory form, or email the maintainer named in the repository. Include what you did, what happened and what you expected. Please allow time for a fix before publishing.
