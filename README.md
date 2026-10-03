# Periodize My Run

A training planner that runs on your own computer: macOS, Windows, or Linux
(including a Raspberry Pi). It reads your Garmin history, builds a plan toward
your goal race, and keeps adjusting it from what you actually do. No AI is
used when it runs: the rules are ordinary code in `engine.py` and `assess.py`.

> **Before you use it**
> - **Not medical advice.** It is a training tool. See a doctor before starting
>   or changing training, and stop for chest pain, fainting or illness with a
>   fever. You run, and follow any plan from it, **at your own risk**.
> - **Not for the internet.** Run it on your own computer or your home network
>   only. Never forward a router port to it or put it on a public address.
> - **Your data is yours.** Everything stays on your computer, and keeping that
>   computer, your backups and the app password safe is up to you.
> - **No warranty.** It is free software provided as is (see LICENSE), it can be
>   wrong, and Garmin can break the connection at any time. Read
>   [DISCLAIMER.md](DISCLAIMER.md); the app asks you to accept it once.

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
  Periodize My Run.
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

Needs Python 3.12 or later and a Garmin account. Download or clone this
repository, then run the installer for your system from its folder.

**macOS**

    ./install.sh

It starts at login and runs at http://localhost:8321, for this computer only.

**Windows 10 or 11** (install Python from python.org first, ticking "Add
python.exe to PATH"). In PowerShell, in the Periodize My Run folder:

    powershell -ExecutionPolicy Bypass -File .\install.ps1

It starts, hidden, every time you sign in, at http://localhost:8321, for this
computer only. The Windows installer has not yet been tested on a real Windows
machine; please report any problem.

**Linux and Raspberry Pi** (Debian, Ubuntu, Raspberry Pi OS, DietPi, or any
system with systemd)

    ./install.sh

It asks you to choose an app password, creates a certificate, and starts the
app at boot, reachable from your home network at `https://<computer's
address>:8321`. The browser warns once about the self-made certificate; that
is expected. To keep it to this computer only instead, run
`PERIODIZE_HOST=127.0.0.1 ./install.sh`.

**By hand, on any system**

    python3 -m venv .venv
    .venv/bin/pip install --require-hashes -r requirements.lock   # Windows: .venv\Scripts\pip
    .venv/bin/python web.py                 # this computer only
    .venv/bin/python web.py --host 0.0.0.0  # your home network (needs an app password first)

All data lives in `~/.periodize-my-run` (database, downloaded files, logs; on Windows
`C:\Users\<you>\.periodize-my-run`), and the key that encrypts your Garmin login is
in `~/.config/periodize-my-run/vault.key`. Delete both to start again.

### Have it as an app

It is a web page, but you can give it its own icon and window:

- **Mac:** open it in Safari and choose File > Add to Dock (macOS 14 or later),
  or in Chrome choose the install icon in the address bar.
- **Windows:** open it in Edge (... > Apps > Install this site as an app) or
  Chrome (the install icon in the address bar), then pin it to the taskbar or
  Start.
- **Phone:** open it in the browser and choose Add to Home Screen from the
  share or menu button. The phone must be on your home network, and the app
  must be installed for your network (the Linux or Raspberry Pi set-up).

## Tips and fixes

**Locked out after wrong passwords.** Five wrong app passwords lock that
device out for 15 minutes; wait, or restart the app to clear it
(`sudo systemctl restart periodize-my-run` on Linux).

**Forgot the app password.** Set a new one on the computer running the app:

    .venv/bin/python web.py --set-password
    # Raspberry Pi installed as user dietpi in /opt/periodize-my-run:
    sudo -u dietpi -H /opt/periodize-my-run/.venv/bin/python /opt/periodize-my-run/web.py --set-password

It takes effect at once and signs every device out.

**Opening the app by a name** (for example `http://raspberrypi.local:8321`)
gives "This address is not allowed" until you allow it once:
`python web.py --allow-host raspberrypi.local`. Addresses like `192.168.1.20`
always work.

**Garmin stopped updating.** Garmin sometimes ends the sign-in. Go to Settings,
Connections, Garmin, disconnect and connect again. If the plan has not updated
for seven days, the app warns you.

**Different port.** Set `PERIODIZE_PORT` before running the installer, for
example `PERIODIZE_PORT=8400 ./install.sh`.

**Moving to a new computer.** Copy `~/.periodize-my-run` and
`~/.config/periodize-my-run/vault.key` across, or restore a backup and connect Garmin
again. A backup never contains your Garmin login or app password.

**Off-site backups.** Download backup in Settings gives a copy with no
secrets. `tools/pull_backup.py`, run on another computer, fetches one every
day into a folder that Google Drive for desktop or iCloud Drive uploads.

**Updating.** Download the new version over the old folder (or `git pull`),
then run the installer again. Your data is kept; the database upgrades itself.
On Linux the installer asks for the app password again (you can enter the same
one); this signs other devices out.

**Stopping or removing it.** macOS:
`launchctl unload ~/Library/LaunchAgents/com.periodizemyrun.app.plist`. Windows:
`Unregister-ScheduledTask -TaskName 'Periodize My Run'`. Linux:
`sudo systemctl disable --now periodize-my-run`. Then delete the folder, and
`~/.periodize-my-run` and `~/.config/periodize-my-run` if you want your data gone too.

**Logs.** The Log tab shows what the app has been doing. The file is
`~/.periodize-my-run/logs/periodize.log`; passwords, tokens and email addresses are
filtered out, but check before sharing it.

## Privacy and security

**Credentials**
- No password is stored. The Garmin password is used once to sign in and is
  dropped; Garmin offers personal apps no sign-in that avoids typing it.
- The Garmin tokens and the notification address are encrypted
  (Fernet: AES with an integrity check) before they are stored. The key is
  in `~/.config/periodize-my-run/vault.key`, outside the data folder and readable
  only by you. A copy of `~/.periodize-my-run` or of a backup contains no usable
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

**Do not expose the app to the internet.** It is built for your own computer
or a home network. Do not forward a router port to it or give it a public
address; for access away from home, use a private network such as Tailscale
and keep the app password set.

On Windows, the app cannot restrict file permissions the way it does on macOS
and Linux, so anyone who can sign in to your Windows account can read its
data. Use a separate Windows account if others share the computer.

## Checks

This repository holds only what is needed to install and run Periodize My Run. The
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
  goals use simpler session rules, and the research behind ultra and mountain
  training is thin (see PRINCIPLES.md, sections 11 and 12). Ultra predictions
  ignore terrain, heat, night and altitude.
- No run/walk plans for complete beginners.
- This is a training tool, not medical advice.

## Reporting a problem

Open an issue at https://github.com/romahony26/periodize/issues: say what you
did, what happened and what you expected, and paste the relevant part of the
Log tab if it helps (check it for anything personal first). Security problems
should be reported privately instead: see SECURITY.md.

## Support

If Periodize My Run helps your running, you can buy me a coffee:
https://buymeacoffee.com/romahony

## Licence and disclaimer

MIT. See [LICENSE](LICENSE): free to use, change and share, with no warranty.
Using Periodize My Run also means accepting [DISCLAIMER.md](DISCLAIMER.md): it is not
medical advice, you use it at your own risk, and its authors are not liable for
any loss or injury, to the extent the law allows.
