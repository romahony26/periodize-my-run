# Periodize

A training planner that runs on your own computer (Mac or Raspberry Pi). It
reads your Garmin history, builds a plan toward your goal race, and keeps
adjusting it from what you actually do. No AI is used when it runs: the
rules are ordinary code in `engine.py` and `assess.py`.

## Features

**Setup wizard (in the browser, three steps)**
1. Connect Garmin: email and password, plus the two-step code if your
   account uses one.
2. Add your races: a goal race and any tune-up races, from 5K to 100 miles.
3. Say how you train: units, running days, long run day, days you cannot
   run, and whether to send workouts to your watch.

It then reads your history and builds the plan, showing progress as it goes.

**Planning**
- Goals: 5K, 5 miles, 10K, 10 miles, half marathon, marathon, 50K, 50
  miles, 100K, 100 miles, any other distance, or no race at all.
- Personal limits (peak week, longest run, heart rate zones) from your own
  history.
- Paces from your current fitness, updated weekly; they follow you, not
  your goal time.
- Week types chosen automatically: build, down, recovery, return, tune-up
  race, taper, race.
- Sessions that progress one step from what you last completed.
- 3 to 6 running days, any long run day, and days you cannot run.
- Race predictions for today and for full preparation.

**Every day**
- Downloads new runs, sleep, HRV, resting heart rate, weight and steps.
- Eases today's fast running by up to about 5% after poor sleep, low HRV,
  a raised resting heart rate, or a heavy day on your feet.
- Counts steps taken outside your runs as background load.
- Optional daily message with today's session.

**Your watch**
- The next 21 days (or 7 or 14) kept on the Garmin calendar as structured
  workouts with pace targets, including strength sessions.
- Checked every four hours (around 02:00, 06:00 ... UTC, each check moved by
  up to 30 minutes at random): changed days are re-sent
  and any workout deleted from the Garmin calendar is put back. Your own
  workouts are never touched.

**Control**
- Drag and drop to swap days, with undo and a warning for hard days back to
  back.
- Mark yourself sick or injured; the plan rests you and brings you back.
- Add a holiday and choose how to run while away: no running, easy runs
  only, easy runs and the long run, sessions only, sessions and the long
  run, or as normal.
- Plan against actual, week by week. Weight trend.
- "How it works" page generated from the live rules and your settings.
- Backup download. Activity log.

**Backups and calendars**
- Nightly backups on this computer, kept daily for 7 days, weekly for 4
  weeks and monthly for 3 months, with restore; a secret-free backup to
  download.
- `tools/pull_backup.py`: run on another computer, it fetches a secret-free
  backup each day into a folder that a sync app uploads (Google Drive for
  desktop, iCloud Drive), so there is an off-site copy with no sign-in inside
  Periodize.
- A calendar file for Apple Calendar, Outlook or Google Calendar.

**Running it**
- Installer for macOS and Raspberry Pi; starts at boot and stays running.
- Catches up after downtime; warns after 7 days without an update.
- Password, login limits and HTTPS for access from other devices.

## How much history it uses

- **Everything, in summary.** One line per activity for every year on your
  account. This is cheap (about one request per 100 activities) and gives
  your best times, your highest sustained mileage, your maximum heart rate
  and your breaks from running. Those set your personal limits.
- **The last 26 weeks, in detail.** Second-by-second files are downloaded
  only for recent runs, because only recent training says how fit you are
  now. Planning itself uses the last 8 weeks.

## Install

Needs Python 3.12 or later.

    ./install.sh

On a Mac it then runs at login at http://localhost:8321, for this computer
only. On a Raspberry Pi the installer asks you to choose an app password,
creates a certificate, and starts the app at boot; open
`https://<pi address>:8321` from any device on your network. The browser
warns once about the self-made certificate.

To run it by hand instead:

    python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
    .venv/bin/python web.py                 # this computer only
    .venv/bin/python web.py --host 0.0.0.0  # reachable on your network

All data lives in `~/.periodize` (database, downloaded files, Garmin login
tokens, logs). Delete that folder to start again.

## Privacy and security

**Credentials**
- No password is stored. The Garmin password is used once to sign in and is
  dropped; Garmin offers personal apps no sign-in that avoids typing it.
- The Garmin tokens and the notification address are encrypted
  (Fernet: AES with an integrity check) before they are stored. The key is
  in `~/.config/periodize/vault.key`, outside the data folder and readable
  only by you. A copy of `~/.periodize` or of a backup contains no usable
  login.
- Limit: anyone who can read all of your user account's files can read the
  key too. Use full-disk encryption on the computer.
- The app password (for access from other devices) is kept only as a salted
  PBKDF2 hash.

**Access**
- From other devices the app requires the app password, set on the device
  with `python web.py --set-password`. Five wrong attempts lock that device
  out for 15 minutes. It refuses to listen on the network without one.
- On the Pi the connection is encrypted with a self-signed certificate.
- Every change must come from the app's own page: cross-site requests,
  forged forms and unknown host names are refused.
- The page runs only its own script file; inline and outside scripts are
  blocked by the content policy.

**Data**
- Nothing is sent anywhere except Garmin and the
  notification address if set (which may not point at this computer).
- Logs and the database are readable only by you; logs are filtered for
  anything shaped like a password, token, key or email address.
- The downloadable backup, and the copies `tools/pull_backup.py` makes,
  contain no secrets.

Do not expose the app to the internet. It is built for a home network.

## Checks

This repository holds only what is needed to install and run Periodize. The
test suite and the checks below are kept with the development copy and are
not included here.

    pip install -r requirements-dev.txt && playwright install chromium   # once
    brew install gitleaks trufflehog                                      # once (or your system's equivalent)
    ./check.sh            # all six stages
    ./check.sh quick      # everything except the browser stage

Run it after every change. It stops with a failure if any stage fails.

| Stage | What it checks | Tool |
| --- | --- | --- |
| 1. Static code | Syntax, unused code, likely bugs, risky constructs | ruff, py_compile |
| 2. Static security | Insecure patterns in the code; known vulnerabilities in the pinned libraries | bandit, pip-audit |
| 3. Security tests | Access control and secrets (`test_security.py`); a red-team suite organised by the OWASP Top 10 2021 (`test_owasp.py`); the OWASP Top 10 2025 additions, the OWASP API Security Top 10 (2023) and the OWASP Web Security Testing Guide areas (`test_owasp_more.py`); hostile input to every route (`test_fuzz.py`) | unittest |
| 4. Feature tests | The planner across runner types and goals; every app function; backups, restores and the calendar file | unittest |
| 5. Interface and usability | A real browser: first-run wizard, every tab, drag and drop, popups, stored-script injection, phone layout, accessibility, keyboard, speed | Playwright, axe-core |
| 6. Secret scanning | No credential, key or token anywhere in the code | gitleaks, trufflehog |

The red-team suite, by OWASP category:

| | Attacks that must fail |
| --- | --- |
| A01 Broken access control | Every route enumerated and called anonymously from another device; spoofed forwarding headers; path traversal; use after logout |
| A02 Cryptographic failures | Secrets readable in the data folder; reading the vault with another key; stored passwords; weak cookie; plain-http or unverified outbound calls |
| A03 Injection | SQL, script, template, header and calendar-file injection through every text field and identifier; dangerous constructs in the code |
| A04 Insecure design | Password guessing; rewriting history; out-of-range values; mass assignment of protected settings; restores that cannot be undone |
| A05 Security misconfiguration | Missing headers; stack traces in errors; debug mode; unexpected methods; inline scripts; listening on the network without a password |
| A06 Vulnerable components | Unpinned libraries; anything loaded from another site |
| A07 Authentication failures | Session fixation; forged session cookies; empty or malformed passwords; two-step codes with no sign-in in progress |
| A08 Integrity failures | Restoring damaged, foreign or hostile backups; oversized archives |
| A09 Logging failures | Security events missing from the log; secrets in the log; a slow log filter; a readable log file |
| A10 Request forgery (server side) | Notification address pointing at this computer, cloud metadata, files or other schemes; redirects |
| Other | Cross-site request forgery on every route; DNS rebinding; oversized and malformed requests; slow regular expressions; two jobs at once; the Garmin password reaching disk |

Beyond the red-team suite, `test_owasp_more.py` covers:

| | Attacks that must fail |
| --- | --- |
| Top 10 2025: A03 Supply chain | Unpinned or unhashed packages; installs from URLs, branches or local paths; `curl \| sh`; code from other sites |
| Top 10 2025: A10 Exceptional conditions | An error inside the access check letting a caller in; database errors showing internals; a crashed job leaving the app stuck; the scheduler dying; odd data from Garmin |
| API1–API10 (2023) | Unknown and malformed object ids; replaying a cookie after logout; secret properties in responses; writing internal properties; oversized requests and ranges; repeated sync requests; unlisted methods and routes; cross-origin sharing; hostile text from Garmin |
| WSTG | Server and version banners; leftover files and comments; TRACE and other methods; HSTS; TLS 1.2+; caching of private responses; cookie attributes and session expiry; parameter pollution; header injection; JSON type confusion; error pages; weak hashes and randomness; impossible values; tab-nabbing links; DOM sinks; secrets in browser storage; clickjacking |

`tools/live_scan.sh HOST` scans a running install from another computer
(nmap, testssl.sh, nikto), as an outside tester would.

No test touches Garmin or your real data: they use temporary folders,
a made-up athlete and stand-ins for the outside services. That also means a
real Garmin login is not covered by the suite.

## Limits

- One athlete per install.
- The Garmin library is unofficial and Garmin can break it.
- The fitness model and the size of the daily pace adjustment are rules of
  thumb, not measurements. A race result is the best evidence it gets.
- It reads what you did, not how you feel, apart from what you mark as sick
  or injured. Override it when you know better.
- Running only, Garmin only.
- Marathon planning is the most developed. 5K, 10K, half marathon and ultra
  goals use simpler session rules. Ultra predictions ignore terrain.
- No run/walk plans for complete beginners.
- This is a training tool, not medical advice.

## Licence

MIT. See [LICENSE](LICENSE): free to use, change and share, with no warranty.
