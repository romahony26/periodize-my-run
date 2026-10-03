# Change log

Every version of Periodize, newest first. Each entry says what was added, changed, removed or fixed.
The app's Change log page is drawn from this file.

## 2.4.1 - 2026-10-03
### Changed
- The Update button at the top of every page is now called Sync, and the wording follows it everywhere: "Synced" with the time, "Daily sync time" in Settings, and the warnings about a failed or overdue sync. "Update" now only ever means a new version of the app.

## 2.4.0 - 2026-10-03
### Added
- Updates from the app. Once the project is public on GitHub, the app checks once a day, at a random time, for a newer version (nothing about you is sent) and shows a notice: Update now, or Dismiss until the next version. Settings, About shows the update status, a Check now button, and a list of versions to switch between, so you can go back to an earlier one and forward again.
- Every update is checked before it is used: downloaded over HTTPS from the project's GitHub, unpacked safely (no file can land outside its folder), its version must be the one asked for, every Python file must compile, and its library list must match the installed one. A version that needs new libraries is installed with the installer instead. A backup is made before every update or switch; nothing is deleted.
- Versions installed this way live in the data folder, because on a Raspberry Pi the app may write nowhere else; the copy the installer put in place starts whichever version was chosen.
- The daily check can be switched off in Settings, About.

## 2.3.0 - 2026-10-03
### Added
- "How accurate are the predictions?" on the Fitness page. For each of your races in the last three years, the prediction is rebuilt from what was known the Monday before and set against your actual time (adjusted to a flat course where the course is known), with the average error and whether the predictions lean cautious or optimistic for you. Each race is worked out once and kept.

## 2.2.0 - 2026-10-03
### Added
- Heat adjustment, off unless you switch it on (Settings, Connections). On hot, humid days fast paces are eased by the widely used temperature-plus-dew-point table, on top of any recovery easing; a dangerously hot and humid day turns the session into an easy run; and once your goal race is within 16 days, the goal card shows the race-day forecast and how much slower to expect. The forecast is read for the hour you usually run, worked out from your runs.
- The weather comes from Open-Meteo (free, no account). The only thing sent is your rough location, rounded to about 10 km, taken from your latest outdoor run. The page never waits for it: forecasts are fetched by the scheduled updates and kept for three hours.
### Fixed
- When a session was turned into an easy run, the Today card said "Paces eased 0.0%"; it now says what changed and why.

## 2.1.0 - 2026-10-03
### Added
- Where your runs come from is now a choice, in Settings, Connections: Garmin (unchanged and still the default), FIT files from a folder, or COROS (experimental).
- FIT files from a folder: .fit exports from COROS, Polar, Suunto, Wahoo or any watch, read at every update, with the full second-by-second detail. Files are recognised by their content, so a renamed file is not read twice. Runs only: no sleep or HRV, and nothing is sent to the watch. The folder can only be chosen on the computer the app runs on.
- COROS (experimental): reads your runs from your COROS account through COROS's unofficial web interface. Written without a COROS watch to test against and tested only with stand-in COROS replies, so it may not work. Your password is sent once (as the hash COROS's own site sends) and never stored; only the access token is kept, encrypted. It never sends anything to COROS, and stops cleanly if COROS replies in a way it does not recognise.
### Changed
- Behind the scenes, the app now reaches watches through one place (watch.py), so other brands can be added without touching the planner.
- DISCLAIMER.md names COROS alongside Garmin.
### Fixed
- The Fitness page could fail to load when two of your race results were at the same distance (the race-spread figure divided by zero). Found by the random-input tests.

## 2.0.0 - 2026-10-03
### Changed
- Periodize is now **Periodize My Run**: in the app, the documents, the brochure and the GitHub project (github.com/romahony26/periodize-my-run).
- The data folder is now `~/.periodize-my-run` and the key folder `~/.config/periodize-my-run`. They are moved from the old names automatically the first time the new version runs, or by the installer; nothing has to be done by hand.
- The background service is now `periodize-my-run` on Linux, `com.periodizemyrun.app` on macOS and "Periodize My Run" on Windows. The installers stop and remove the old one.
- Unchanged, so nothing breaks: the database and backup file names inside the folder, and the PZ prefix on workouts on your Garmin calendar.

## 1.21.0 - 2026-10-03
### Added
- Windows support: an installer (install.ps1) that starts Periodize, hidden, every time you sign in, for that computer only; the app's one-copy-only lock now works on Windows too. Not yet tested on a real Windows machine.
- Terms of use and disclaimer (DISCLAIMER.md): not medical advice, use at your own risk, your data and its security are yours, not for the internet, no promises about accuracy, Garmin's interface is unofficial, and a limitation of liability. New installs accept it in the setup wizard; existing installs see a one-time notice on the Plan page. It can be read any time under Settings, About Periodize.
- README: installing on macOS, Windows and Linux; having it as an app with its own icon on a Mac, on Windows and on a phone; tips and fixes (locked out, forgotten app password, opening it by name, Garmin stopped updating, moving computer, updating, removing it, logs); clear notices that it is not medical advice, not for the internet and used at your own risk.
### Changed
- The season outline always labels its last week, so the latest date sits at the right-hand end.

## 1.20.2 - 2026-10-03
### Removed
- The "On your phone" card in Settings. Its Send a test message button now sits under the daily message address in Advanced.

## 1.20.1 - 2026-10-03
### Added
- The Buy me a coffee link in Settings (About Periodize) and in the README.

## 1.20.0 - 2026-10-03
### Added
- The season outline shows each week's distance above its bar and marks races under their week (★ goal race, ● tune-up), with a list of the season's races and the week each falls in. On a phone it scrolls sideways.
- An "About Periodize" card in Settings: the version, what changed, the MIT licence, how to report a problem (a link to open an issue), how to report a security problem privately, and a Buy me a coffee link once its address is set.
- README: how to report a problem.
### Changed
- SECURITY.md points to the private security report form instead of an email address that was never given.
### Fixed
- A backup you had made earlier the same day could be deleted when you restored from it: the restore's safety copy counted as the day's latest backup, and the thinning removed the rest. Now every backup from today is kept until tomorrow's thinning, and a safety copy never takes the place of a day's real backup.
- "The latest backup of the day" is now decided by the time it was made. Before, the nightly backup always counted as the latest, because of how the file names sort.

## 1.19.0 - 2026-10-03
### Added
- Trends on the Fitness page. Threshold pace (speed), Race-specific endurance (the endurance base), Aerobic drift (durability) and Steps outside your runs each have a Trend button showing up to 26 weeks, and a tag saying whether each is improving, steady or slipping over the window that suits it: speed over 6 weeks (steady within 1%), endurance base over 4 weeks, durability over the last six long runs, steps over 7 days against your normal.
- The weekly history behind the trends is rebuilt from your past runs, so the charts reach back before the app was installed. It is kept up to date by the daily update.
- A Recovery trends card: 7-day heart-rate variability, resting heart rate and sleep over 12 weeks, each against your normal.
- The race predictor has a "Last 6 weeks" column showing how each prediction has moved: short races follow speed, long races also endurance, so it shows which kind of fitness you are gaining.
- PRINCIPLES.md: fitness as three things (speed, endurance base, durability), each with its trend window.

## 1.18.0 - 2026-10-03
### Added
- 5K and 10K goals get a taper: the week before race week drops to about 70% with a short session kept, about 8 to 14 days in all.
- One of the two weekly strength sessions now includes plyometrics (pogo hops, skips for height, bounds), which the research links with better economy and faster 5K times.
- Hilly goal races: every third week of the specific phase, the long run includes 15 to 30 minutes of steady downhill running, which protects the legs against downhill muscle damage for weeks after.
- Course pacing marks every sustained climb of 20% or steeper for walking in races of three hours or more.
- Ultra race-day notes: at least 30 to 50 g of carbohydrate an hour from the start, start slower than feels necessary, no ibuprofen (with the trial behind it), and naps under 30 minutes and banked sleep for races through the night.
- PRINCIPLES.md: new sections on 5K and 10K and on ultras and hilly trail races (75 principles in all), each graded honestly; the evidence for ultras is mostly laboratory, race-record and survey data.
### Fixed
- A fuel-practice note no longer replaces another note on the same long run.

## 1.17.0 - 2026-10-03
### Added
- Fitness fades during a break: after 10 days without a run the fitness estimate eases by 0.35% a day, up to 12%, following the detraining research, so your first paces back match what you can do now. Before, it could fall by only 0.5% a week.
- A graded return after any break of two weeks or more, spotted from your runs: about half your usual volume, then three quarters, all easy, for about as long as the break lasted.
- When warning signs persist (three or more on one morning, or one on three mornings running), today's session becomes an easy run of the same distance, on the watch too. The planned session is still shown.
- Race-week guidance on the calendar: carbohydrate loading worked out from your Garmin weight for the two days before a marathon or longer, and race-day notes on caffeine, drinking to thirst, painkillers and shoes.
- Every scheduled contact with Garmin (the daily update and the four-hourly watch check) is moved by its own random amount, up to 30 minutes either way, so installs do not all reach Garmin at once.
### Changed
- From age 50 (read from your Garmin profile), a down week comes every third week instead of every fourth, unless you have set this yourself.
- Long runs are kept to about three hours, except for ultra goals.
- Strength work drops to one session a week in the race-specific phase.
- PRINCIPLES.md and How it works describe all of the above; four of the known gaps are closed.

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
