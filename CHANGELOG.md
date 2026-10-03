# Change log

Every version of Periodize, newest first. Each entry says what was added, changed, removed or fixed.
The app's Change log page is drawn from this file.

## 1.16.2 - 2026-10-03
### Changed
- PRINCIPLES.md rewritten: 60 principles in 11 sections, each matched to what the planner actually does, with the strength of the evidence behind every research finding (strong, moderate or limited). New sections on foundations (consistency, your own baseline, trends, agreeing signs), durability, injury risk, the shape of a season and measurement limits.
- References checked against their published records (title, authors, journal and main finding); the few still cited from memory are marked. Newly cited: Raysmith and Drew 2016, Doherty 2020, Haugen 2022, Muniz-Pumares 2024, Silva Oliveira 2024, Smyth and Lawlor 2021, Llanos-Lagos 2024, Hellard 2006, Gillinov 2017, Riegel 1981 and others.
### Added
- A "Known gaps" section listing where Periodize does not yet follow the evidence: fitness after a long break, how you feel, the return after a light week, heat, age and sex, and low energy availability.

## 1.16.1 - 2026-10-03
### Added
- An MIT licence (LICENSE), so anyone may use, change and share Periodize.

## 1.16.0 - 2026-10-03
### Added
- A second red-team suite (`tests/test_owasp_more.py`, 46 attacks): the two categories new in the OWASP Top 10 (2025), the OWASP API Security Top 10 (2023), and the OWASP Web Security Testing Guide areas that CREST-accredited testers follow.
- `tools/live_scan.sh`: scans a running install from another computer with nmap, testssl.sh and nikto.
### Fixed
- Logging out now ends the login on the server too. Before, a copy of the login cookie taken before logout kept working until it expired. Setting a new app password now signs every device out. Everyone must log in once more after this update.
- Races are checked when saved: a date from 1990 to five years ahead, 0.5 to 200 miles, a name of up to 120 characters, a goal or tune-up priority, and a goal time like 3:00:00.
- The four-hourly watch check treats a malformed entry from Garmin as unreadable instead of failing on it.
- The encrypted connection on a Raspberry Pi now offers only modern ciphers over TLS 1.2 (forward secrecy with authenticated encryption), removing the older CBC ciphers flagged by TLS scanners (LUCKY13).

## 1.15.0 - 2026-10-03
### Removed
- The Google account sign-in, Google Calendar sync and Google Drive backups, with their cards in Settings and restoring from Drive. An upgrade deletes any stored Google sign-in and settings. Nothing in Periodize talks to Google any more.
### Added
- `tools/pull_backup.py`: run on another computer, it fetches a backup each day (the same secret-free file as Download backup) into a folder that a sync app uploads, such as Google Drive for desktop or iCloud Drive. Copies are thinned like the app's own backups.
### Changed
- The calendar file has its own card under Connections. It works with Apple Calendar, Outlook and Google Calendar, imported by hand.

## 1.14.1 - 2026-10-03
### Changed
- Opened at a network number such as 192.168.1.20, the Google account card now says its sign-in will not work there, because Google refuses that return address, and points to the Google Drive backups card, which signs in with a code and needs no return address.

## 1.14.0 - 2026-10-03
### Added
- Connect Google Drive for backups on its own, with a short code: the app shows a code, you enter it at google.com/device on your phone or any computer, and backups start. This works on a Raspberry Pi at a home network address, where the full Google sign-in cannot return to the app.
- The first Drive copy goes up as soon as Drive is connected, and Drive backups switch on by themselves.
- Disconnect Google Drive, which also cancels the permission at Google. Copies already in Drive stay there.
### Changed
- The Google Drive backups card no longer needs the Google Calendar sign-in. That sign-in still works for Drive if you used it.
### Fixed
- Four checks that failed on some days of the week: they assumed today had a session, or that the next hard session was paced by speed rather than heart rate.

## 1.13.0 - 2026-10-02
### Added
- A Garmin calendar check every four hours, at 02:00, 06:00, 10:00, 14:00, 18:00 and 22:00 UTC. It sends any changed workouts and puts back any that are missing from the Garmin calendar, such as one deleted in Garmin Connect. If the calendar cannot be read, it sends changes only.
- 21 days as a choice for "Days kept on the watch".
### Changed
- The watch now keeps the next 21 days by default (was 7). The plan always reaches far enough ahead to fill it.

## 1.12.0 - 2026-10-02
### Added
- A 1 minute rest between the warm-up and the hard part of every session: threshold, intervals, 200s, sharpeners, midweek marathon and half marathon pace, and the aerobic run by heart rate. It shows in the session text and is a rest step on the watch. Long runs, races and the aerobic test are unchanged.

## 1.11.0 - 2026-10-02
### Removed
- The race fitness index: its figure and two charts on the Fitness page, and its column in race results. Race predictions are unchanged, and age grade remains for comparing results.
### Changed
- The Fitness page card now shows Garmin's VO2max estimate only.

## 1.10.0 - 2026-10-02
### Added
- PRINCIPLES.md: the training principles the app is built on, written in the project's own words, with each one marked as research, coaching convention or the project's own choice.
### Changed
- The monthly heart-rate test is now called the aerobic test. Existing tests and settings carry over.
- The explanation of aerobic training in How it works is rewritten in the project's own words.
### Removed
- Text and references drawn from individual coaches' books, documents and videos.

## 1.9.1 - 2026-10-02
### Added
- A product brochure (docs/Periodize-brochure.pdf), built by `python tools/brochure.py` from the app itself: fresh screenshots of a made-up athlete, the feature list, and the version and latest changes from this file.
- A check that fails when the brochure is older than the current version, so it is rebuilt with every release.

## 1.9.0 - 2026-10-02
### Changed
- Freshness and the daily easing now read each marker over the window the research supports. Sleep counts from last night alone, so one bad night eases today's session and a normal night clears it. HRV and resting heart rate count as 7-day averages against your normal.
- A night an hour or more under your normal sleep now eases the session. Before, a single night only counted when it was under 5 hours.
- The day popup shows last night's sleep beside your normal, and the 7-day HRV and resting heart rate beside your normal and last night's reading.

## 1.8.2 - 2026-10-02
### Changed
- The score beside a run is labelled "Execution score", in the run popup and in the History table, so the number is never shown on its own.

## 1.8.1 - 2026-10-02
### Added
- The execution score explains itself: the run popup says what the score means, why this run got it, how many points each kind of running cost, and the pace that separates easy, moderate and hard.
- A tooltip on every score.

## 1.8.0 - 2026-10-02
### Added
- `--always-login on`: require the app password even from the computer the app runs on.
- SECURITY.md, with how to report a problem.
### Changed
- Security hardening and more robust handling of unexpected input.
- Installer and service hardening.

## 1.7.0 - 2026-10-02
### Added
- Missed sessions: a session day that passes with no run is moved to a later day that week, where one fits without putting hard days together. The day is marked with ↻.
- Race pacing plan: add a race's course as a GPX file and get an even-effort split for every mile or kilometre, allowing for the hills.
- Climb targets for the week and the long run when the goal race is hilly.
- A race's total climb, from its course or entered by hand.
- Real maps for runs, from OpenStreetMap, with zoom buttons. Off by default; switched on under Connections.
### Changed
- A missed session that was moved is shown in History as moved, not scored as missed.

## 1.6.0 - 2026-10-02
### Added
- Change log page listing every version and what changed in it. The current version is shown in Settings.
- Connections section in Settings with a card each for Garmin, your Google account, Google Calendar and Google Drive, each showing its status.
- Step-by-step Google setup with a copy button for the redirect address.
- A switch to keep the plan on Google Calendar on or off, separate from Drive backups.
### Changed
- Google Calendar and Google Drive are set up under Connections. The old Calendars card is gone and the Drive switch has moved out of Backups.
- The calendar ID can be changed after connecting, without entering the client details again.
- Settings layout: Advanced options sit in columns with the Save button beside them, and cards no longer stretch to leave blank space.

## 1.5.0 - 2026-10-02
### Removed
- Effort and soreness ratings on runs, with the note field, the Felt column in History, and the two watch-outs that used them.
- Reading effort ratings made on the watch from Garmin.

## 1.4.0 - 2026-10-02
### Added
- Fitness, fatigue and form charts show the numbers for the day under the pointer. Works with touch and the arrow keys.
- A fatigue line beside fitness and form.
- The pace and heart rate charts in the run popup show time, pace and heart rate under the pointer.
- A Garmin icon on every completed run (calendar, day popup, History, run popup) that opens the activity in Garmin Connect.

## 1.3.0 - 2026-10-02
### Added
- Fitness, fatigue and form from daily training load.
- Season outline: every week to the goal race.
- Watch-outs: a run more than 10% longer than the longest of the previous 30 days is flagged.
- Aerobic drift on long steady runs.
- Fuelling outline on planned runs of 75 minutes or more.
- Age grading of road race results (Alan Jones's 2025 standards).
- The watch's own threshold estimate, shown and used as evidence while under six weeks old.
- Shoes with distance counted from your runs.
- Add to Home Screen on a phone, and a test button for the daily message.
### Changed
- Treadmill runs are scored on heart rate and left out of pace evidence.

## 1.2.0 - 2026-10-02
### Added
- Run popup: start time, heart rate, load, Garmin training effect, pace and heart rate charts, and the route outline.
### Changed
- Execution score now uses a published load measure (Lucia's TRIMP: easy, moderate and hard minutes weighted 1, 2, 3). Too much counts the same as too little.

## 1.1.0 - 2026-10-02
### Added
- History page with an execution score for every planned session.
- Fitness charts show each value under the pointer.

## 1.0.0 - 2026-10-01
### Added
- Weekly planning from Garmin data toward a goal race from 5K to ultra, with three provisional weeks ahead.
- Daily pace easing from 7-day trends in HRV, resting heart rate and sleep.
- Workouts and strength sessions sent to the Garmin calendar.
- Setup wizard, drag and drop between days, and sick, injured and holiday handling.
- Race predictor, race results with CSV import, and the race-day forecast.
- Monthly heart-rate tests and heart-rate aerobic runs.
- Nightly backups kept for 7 days, 4 weeks and 3 months, with copies to Google Drive and three kinds of restore.
- Google Calendar sync and a calendar file for other calendar apps.
- Encrypted storage of Garmin and Google tokens; no passwords stored.
- How it works page that explains every number.
### Removed
- The coach chat and its use of an outside AI service.
- The "What your races taught you" section.
