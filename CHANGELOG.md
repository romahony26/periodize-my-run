# Change log

Every version of Periodize, newest first. Each entry says what was added, changed, removed or fixed.
The app's Change log page is drawn from this file.

## 2.10.2-beta.12 - 2026-10-25
### Added
- The plan now shows about three months ahead (13 weeks, up from 3; the setting goes up to 16). The weeks after the first are provisional and are redone as real weeks come in.

### Changed
- A week with four or more days away on a trip or holiday is now the down week: it restarts the count of build weeks, is labelled as such, and the next week goes back to building where you left off, with no second down week and no return week. Before, the trip week was labelled a build week with a target the trip could never allow, a down week followed it, and a trip that cut the week below half the usual volume would have started a return week.
- The plan projects forward from what a trip week will really hold, not the target set before the trip trimmed it.

## 2.10.2-beta.11 - 2026-10-25
### Fixed
- The plan outline to the goal race assumed the full step was never earned. Each projected week now counts as run as planned, so after three projected weeks the outline climbs at the full step, as it will if you run the plan.

## 2.10.2-beta.10 - 2026-10-25
### Changed
- Past the most you held in the last year, the weekly step is now the full 6% once you have run at least 95% of the planned miles in each of the last three weeks, and stays at half (3%) otherwise. A warning sign still holds the volume level. It rewards what you have shown you can hold, not a watch reading. (The code arrived in 2.10.2-beta.9, tagged without its changelog entry.)

## 2.10.2-beta.8 - 2026-10-25
### Added
- A race's importance (goal race or tune-up) and goal time can now be changed on the Races page, with a note when more than one goal race is set, and the plan says so too.
- A marathon goal time now sets how much volume the plan may build toward: 55 miles a week for 3:00, a mile more for each minute faster, within 40 and 90, but never past half again on the most you have held in the last three years. The weekly step is unchanged and a warning sign still holds it.
- A midweek medium-long run (about a quarter of the week, 8 to 14 miles) in marathon, half-marathon and ultra builds, alternating with the heart-rate aerobic run.

### Changed
- Two warning signs in a single week now hold the volume level; a recovery week needs them for two weeks running, or three at once.
- Easy pace at a fixed heart rate is shown but no longer counts as a warning sign (heat, wind, hills and watch error move it more than the 3% it used).
- The learned taper and the "miles or hard running" adjustment are shown but no longer change the plan unless `apply_learned` is switched on.
- PRINCIPLES.md corrected: Garmin HRV accuracy (principle 50), the HRV-guided training result (51), and wind, which the app has adjusted for since 2.10.1 (91).

## 2.10.2-beta.7 - 2026-10-25
### Changed
- Recovery signs can now only slow the build, never speed it. Past the most you held in the last year the step is half the weekly rate whatever the readings. Steady HRV and resting heart rate are shown but change nothing; a warning flag, or HRV and resting heart rate both more than one spread off your own normal, holds the volume level. The test is against your own mean and spread over the four weeks before, replacing the fixed percentages; sleep and easy pace are no longer used to call recovery good. HRV-guided trials used the markers to hold intensity back, not to add volume, and watch readings are too noisy for a green light.
- An old peak now counts less with time: the highest 8-week block you have held counts in full for three years after it ended, then fades, and is gone eight years after. It was treated as a fixed ceiling whatever its age.
- The longest-run window ignores days away (a trip, a holiday, illness or injury), so a long run skipped for a trip does not make the first long run back look like a jump.
- The citations in the app and in PRINCIPLES.md are corrected: Nielsen 2014 found only a non-significant trend; Damsted 2019 found the extra risk in the following three weeks and not later; the 2025 paper is Frandsen and colleagues; Impellizzeri 2020 is cited for the problems with the ratio. The 20% limit, the down-week cadence and the hard-day spacing are labelled as conventions.

### Added
- A course of a fluoroquinolone antibiotic (ciprofloxacin, levofloxacin, moxifloxacin, ofloxacin and others) named in the note of a sick, injured or recovering entry now brings 60 days of easy, flat running after it ends, as the recovering "tendon" setting does. Tendon rupture risk is highest in the first weeks and still raised at 60 to 90 days.

## 2.10.2-beta.6 - 2026-10-25
### Changed
- Your recovery now sets how fast the volume climbs. Each week the app reads your HRV, resting heart rate, sleep and easy pace against your own normal. While all of them are steady or better, a build week rises by the full weekly rate (6% by default), even past the most you held in the last year. While they are only fair (one drifting, or too little data), the step past that level is half (3%). When a warning flag is up, the volume is held level until it clears. Replaces the fixed 2% step of 2.10.2-beta.5. The ceilings are unchanged: the phase cap, 20% above your best of the last three weeks, and the level you have held before.
- Later weeks in the plan assume fair recovery, since how you will recover is not known yet; the plan is redone as it comes in.

## 2.10.2-beta.5 - 2026-10-25
### Changed
- Volume now climbs steadily back toward a level you have held before. Past the most you held for eight weeks in the last year, each build week rises by a small step (a third of the weekly rate, 2% by default: about a mile), up from half the rate (3%), and the week says what it is rebuilding toward when your history holds a higher level. The ceilings are unchanged (the cap for the phase, 20% above your best of the last three weeks, and the level you held before without breaking down afterwards).

### Fixed
- Volume stalled once past the level held in the last year: a down week pulled the four-week average down, so each build started a little lower than the last and the totals hovered. A build week now starts from the best three-week average of the last six weeks, and from last week if it was a build week, so volume climbs across down weeks.

## 2.10.2-beta.4 - 2026-10-25
### Added
- A final check on every week, whatever has changed it: no two hard days (quality session, long run, race) are left side by side. The later quality session becomes an easy run; the long run and a race never move for it.
- The rules for rebuilding a week when a day is lost are written in PRINCIPLES.md ("When a day is lost"), marked as coaching convention and this project's own choices.

## 2.10.2-beta.3 - 2026-10-25
### Changed
- When the long run moves to the day before a day away, the week's rest day goes and the days from it to the long run each move a day earlier, so the week keeps both its quality sessions and its long run, each apart from the next, with the rest day on the day away. Only when there is a rest day earlier in the week and every day between is at home; otherwise the long run swaps places with an easy day as before.

## 2.10.2-beta.2 - 2026-10-25
### Fixed
- When the long run moves off a day away, a quality session on the day before or after it now becomes an easy run, so the long run never follows or precedes a hard day (a threshold session on Friday had left Saturday's long run on tired legs).

## 2.10.2-beta.1 - 2026-10-25
### Fixed
- A long run that fell on a work trip or holiday day was turned into a short optional easy run, so the week had no long run, and moving that day by hand could not bring it back. The long run now moves to a day at home in the same week: the other weekend day first (Sunday's goes to Saturday), then the nearest day, the day before first. The easy or rest day it replaces takes its place on the day away. Only easy and rest days are used, never a day of illness or injury, and a trip that covers the whole week still turns every run optional.

## 2.10.1 - 2026-10-25
### Fixed
- Code scanning: the "information exposure through an exception" alerts in web.py are cleared (see 2.10.1-beta.10).
- Sleep, resting heart rate, HRV and steps held in the saved Garmin records now reach the daily table (see 2.10.1-beta.9).
- A change made while a replan, readiness check or push was running is no longer dropped (see 2.10.1-beta.8).
### Changed
- Everything from the 2.10.1 betas, listed below: the daily adjustment setting, wind and Met Éireann warnings, and the Garmin history download that no longer delays a sync.

## 2.10.1-beta.10 - 2026-10-25
### Fixed
- Code scanning: the five "information exposure through an exception" alerts in web.py (race course, race log import, update, COROS sign-in and backup). The page already showed only messages this app wrote; they are now read from the error's own message rather than its text form, so no library or stack detail can reach the page. What you see is unchanged.

## 2.10.1-beta.9 - 2026-10-25
### Fixed
- Sleep, resting heart rate, HRV and steps held in the saved Garmin records now reach the daily table. The saved records go back to May 2023, but the daily table only held what the ordinary sync had read, from February 2026. Each sync now copies what is missing from the saved records, asks Garmin for nothing, and never replaces a value already held. The last three days are left to the ordinary sync.

## 2.10.1-beta.8 - 2026-10-24
### Changed
- The download of daily Garmin records now fills gaps only: a day and kind not yet held, or held from before the day ended. Today is never read, because the ordinary sync already has it. With no gap it makes no request to Garmin at all.
- It runs in a thread of its own, started by the scheduler, and no longer inside the sync job. It stops between requests the moment a sync starts and carries on once the sync is over, so it cannot delay or lengthen a sync or hold its lock. When Garmin limits the requests it rests for an hour.

### Fixed
- A change made while a replan, readiness check or push was running (a setting, a race, a holiday, a moved session) was silently dropped, so the plan stayed out of date until the next sync. On a busy or slow machine two quick changes could do it. Now it runs straight after the current job, once however many were asked for, with nothing in between that looks idle. Sync and first-time setup are still refused while another job runs. A job that crashes before it can report now always lets go of the lock and lets the next one run.
- Starting a job now returns only once the job has begun, so a page or a test that looks at once never sees "idle" before it starts.

## 2.10.1-beta.7 - 2026-10-24
### Changed
- Saving the daily Garmin records now runs at the very end of the sync, after the plan, the push to the watch and the morning message, and in slices of at most 30 minutes, so a long download of history can never delay them. A failure in it no longer makes the day's sync count as failed.

## 2.10.1-beta.6 - 2026-10-24
### Added
- Wind now slows fast running. The allowance is a model anchored to Pugh's 1971 measurement that air resistance is about 7.5 to 8% of the energy cost of running at 21.5 km/h and that the cost of running into a wind rises with the square of its speed: on a loop route, against the wind half the way and with it the other half, at the same effort, with the forecast wind scaled to running height. About 2% at a forecast 20 km/h, 4.5% at 30 and 7% at 40, up to 15%. It adds to the heat allowance, counts in the choice of best start hour, and is shown on Today with the gusts.
- Met Éireann weather warnings, read from its public feed (www.met.ie; no account, nothing about you sent; your county is worked out on this computer from the rounded location the weather already uses). The warnings for your county, its province or all of Ireland are shown on Today and in each day's detail exactly as issued, with the credit and licence statements Met Éireann requires, and are removed when they expire. If the feed cannot be read for three hours none is shown and the page says so. An Orange or Red warning for wind, snow or ice, thunderstorm, fog, heat, low temperature, rain or flood that covers your start hour turns today's run into an easy one (Red: no outdoor run). Yellow warnings are shown and change nothing.
- A forecast of thunder, freezing rain, heavy snow, or wind of 55 km/h (gusts 90 km/h) or more at your start hour also turns the run into an easy one with advice to use a treadmill.
- "Wind and weather warnings" in the explanations.
### Changed
- The weather switch now also covers the weather rules without the recovery adjustment: with "Ease paces on poor recovery" off, wind, heat and the warnings still apply.
### Fixed
- The notes on the weather said wind had no effect once temperature was allowed for, and cited a paper (El Helou and colleagues, 2012) that never looked at wind. Both are removed.

## 2.10.1-beta.5 - 2026-10-24
### Added
- Everything else Garmin keeps for each day is now saved whole (compressed) instead of three numbers being picked out and the rest thrown away: sleep stages, stress, Body Battery, breathing, blood oxygen, Training Readiness and Status, VO2max, the all-day heart rate, floors and intensity minutes. The newest days come first and it works back, in time-boxed slices after the daily sync, until 240 days in a row hold nothing. It carries on by itself after a restart or a Garmin rate limit, leaves out a kind that Garmin will not give for the account, and re-reads the last two days because a day is not finished until the next morning. Settings shows how far back it has got. Nothing uses the records yet.
### Changed
- The database gains a garmin_raw table (schema 21).

## 2.10.1-beta.4 - 2026-10-21
### Changed
- The app now syncs with Garmin every hour instead of every four hours. Each hourly sync happens at its own random time past the hour (anywhere from 0 to 59 minutes), so installs do not all reach Garmin together.

## 2.10.1-beta.3 - 2026-10-21
### Fixed
- Updated certifi from 2026.7.22 to 2026.10.19, which fixes the known vulnerability PYSEC-2026-4320.

## 2.10.1-beta.2 - 2026-10-21
### Changed
- The Daily adjustment slider also governs the two weeks after an illness. Before, any one warning sign in that window turned a session into an easy run. Now it takes 1 point at 100%, 2 at 75%, 3 at 50% (the default) and 4 at 25%, and nothing at 0%.

## 2.10.1-beta.1 - 2026-10-21
### Added
- "Daily adjustment" slider in Settings (0 to 100%, steps of 25). It sets how much poor sleep or recovery changes a session: 0% never changes it, 100% is the full rules as before.
### Changed
- The default is 50%. A poor night's sleep now eases fast paces but no longer replaces the session with an easy run; that takes more warning signs together (5 points at 50%, against 3 before). The three-mornings rule applies at 75% and above.

## 2.10.0 - 2026-10-18
### Fixed
- Code scanning: restoring a backup now takes the file from the backups folder's own listing, and installing a version checks that its folder is inside the versions folder, so neither can be pointed elsewhere by the request.
- Code scanning: a failed Garmin sign-in, Garmin code, backup or restore no longer sends the library's error text to the page. The page gets a fixed message and the detail (with passwords and tokens removed) goes to the log.

## 2.10.0-beta.18 - 2026-10-18
### Added
- "Work trip / jet lag" next to Holiday on the Races page. For the dates you give, every run becomes a short easy run (up to 5 miles) marked optional, strength reminders are dropped and rest days stay rest. Skipped runs on a trip are not counted as missed, and the time is not counted against a training block. Race days are left as planned.

## 2.10.0-beta.17 - 2026-10-16
### Added
- "Extra volume in build weeks" in Settings, under Advanced: off (0%) by default, or +5%, +10% or +15%. It raises build weeks after the usual 20% rise limit, so it goes past what the research supports (Damsted and colleagues, 2019); the week's explanation says so. Return, down, taper and race weeks are never raised.

## 2.10.0-beta.16 - 2026-10-14
### Added
- Quick actions on today's card: "Swap with tomorrow" and "I'm unwell today". They appear only on a day with a planned run that has not been done.
- The settings and Fitness tab rows work from the keyboard: arrow keys, Home and End move between tabs, and only the selected tab is a tab stop.
- `tools/deploy.py` puts a tag on the Pi, checks that it answers as the right version with the state the page needs and no tracebacks, and puts the old version back if it does not. It also keeps a copy of the tests, which are not in git.
- Every page and tab is measured in light and dark at three widths for text under 11 px, text cut off, cards on top of each other and empty cards; dark mode is checked for contrast; tap targets are checked on a phone; and card positions are compared with a recorded baseline.
- Coverage of the app's code rose from 85% to 91%: every Garmin read is tested against a stand-in client in the real reply shapes, and so are the notification rules, when syncs are due and each way today's session is changed.
- `tools/mutation_check.py` makes small changes to the rules and reports which the tests do not notice. The first sample of 70 found 26 unnoticed (63% caught); after pinning the numbers that define the pace zones, race factors and thresholds, and the day-part and sleep comparisons, the same sample catches 83%.
- Generated cases check that the race equivalence is its own inverse, that rank correlation is bounded, and that every day the planner can produce becomes a valid Garmin workout and a FIT file an independent reader accepts.
### Changed
- The Fitness page's loading cards show a placeholder that holds their height, so the page no longer jumps when they fill, and say "Loading" to a screen reader.
- The Fitness, fatigue and form chart starts at your first run instead of drawing weeks of flat zeros before it.
- Small text is at least 11 px everywhere, and the small icon links on a day are 30 px square, so they are easier to hit on a phone.

## 2.10.0-beta.15 - 2026-10-14
### Fixed
- Principles 54 and 54a gave the wrong source for how long respiratory illness lasts in athletes and for the "neck check". The figures (7.1 days; 20% of illnesses costing more than a day of training; only 4 of 54 studies reporting days until return to sport) come from Snyders and colleagues (2022), and the neck check's weak basis from Hull and colleagues (2020). Derman and colleagues (2022) is a review of risk factors, and it lists increased training monotony and lack of tapering among them.
- Principle 70 (start slower in an ultra) was marked as research and named no study. It now cites Suter and colleagues (2020), and the part the abstract does not support is marked as coaching practice.
- Durability studies Maunder (2021) and Matomäki (2023) were cited but missing from the reference list; now added, with the limit that Matomäki studied adults on a bicycle.
- Several references had wrong or partial titles, authors or pages; they now match their published record (Lucia 2003, Thomas 2016, Mountjoy 2023, Impellizzeri 2020).
### Added
- `tools/check_references.py` checks the principles and references against each other, and with `--live` against Europe PMC and Crossref (113 of 122 matched by the tool, 6 are books, data or notices, and 4 remain marked from memory because no index holds them). It runs with the other checks.

## 2.10.0-beta.14 - 2026-10-14
### Changed
- On a phone, today's session now comes before the goal card on the Plan page. The goal card shows the forecast gap in one line and keeps how it is built under "How this forecast is built".
- The Fitness page is in four sections, Now, Progress, Predictions and Records, with a tab row; it was one scroll of 19 cards (about 3,900 px) and each section is now about 800 to 1,450 px. Your last section is remembered.
- Long grey explanations on the Fitness page are folded under "What is this?"; the numbers stay in view.
- Empty lists (shoes, race results) shrink to a heading and one line, with the form under it.

## 2.10.0-beta.13 - 2026-10-14
### Added
- Checks only, no change to the app: the daily job is tested end to end against a stand-in Garmin (order of steps, nothing sent when sending is off, a refusal stops cleanly, other sources never call Garmin), and every page and Settings tab is checked at phone, tablet and desktop width for sideways scroll, anything wider than the screen, anything fixed to the screen and console errors.

## 2.10.0-beta.12 - 2026-10-14
### Fixed
- In a race week, the fixed sharpener and shakeout could land on a day you had marked as one you cannot run. Blocked days are now left as rest in a race week too. Found by a randomised test of the planner over thousands of generated athletes, which now runs with the other checks.
### Added
- Tests for code nothing reached before (found with coverage): the taper and miles-or-hard learning, the Explain my plan page and the trend helpers.
- `tests/test_live.py` checks the real Open-Meteo and GitHub replies still match what the app expects. It runs only with `LIVE=1`.

## 2.10.0-beta.11 - 2026-10-14
### Changed
- The top right panel switches to tomorrow only for a run of half a mile or more, so a warm-up or an accidental start does not count as the day's run.
### Fixed
- The kept race forecasts were listed among the settings in a settings backup. They are history, not a setting: they come back with a full restore and are no longer in the settings file.

## 2.10.0-beta.10 - 2026-10-14
### Changed
- The rules were tested against a public training log of 74 competitive runners with 575 recorded injuries (DataverseNL, CC0). What held: a jump in the longest run (1.33 times the injury rate), a very hard rated session (1.89 times), and, weakly, a week 20% above the best of the last two (1.25 times). What did not: training monotony (1.06 times, no signal) and a poor rating after a run (fewer injuries, not more).
- A very hard effort rating on your watch (9 or 10 out of 10) still counts as a recovery sign, but a "weak" feel alone no longer does.
- The monotony watch-out is removed; monotony and strain are still shown on the Fitness page.
### Added
- A note on the Plan page when you have run on each of the last seven days: weeks with no rest day went with about 1.3 times the injury rate in that log.
- `tools/validate_injuries.py` repeats the test, and principles 109 to 112 give the numbers and their limits.

## 2.10.0-beta.9 - 2026-10-14
### Changed
- The top right panel now switches to tomorrow's session as soon as any run is logged today, whatever its length. The 70% rule was removed: the app plans one run a day, so there is no second session to wait for.

## 2.10.0-beta.8 - 2026-10-14
### Added
- Once today's run is done, the top right panel of the Plan page shows tomorrow's session instead of today's: its steps and paces, what it is for, the hour the weather suits, and a line with what you ran today. A run counts as done when at least 70% of the planned distance is logged, or any run on a day with nothing planned. A short run of a planned long one leaves today's card in place.

## 2.10.0-beta.7 - 2026-10-14
### Fixed
- The Plan page was broken in 2.10.0-beta.1 to beta.6: the new Settings save bar reused the name of the small bars that show each day's score, so 21 of them turned into a large bar fixed across the bottom of the screen and the day cards lost their bars. The save bar and the on/off switches now have their own names, and a test fails if any page has a fixed element other than the tab bar, toast and dialogs.

## 2.10.0-beta.6 - 2026-10-14
### Fixed
- The Plan scorecard counted a week the plan only partly covered (the app's first week, for example), which made it look as if you ran 150% of the plan. A week now counts only when the plan covers at least six of its days.

## 2.10.0-beta.5 - 2026-10-14
### Added
- A Plan scorecard on the Fitness page: the last 12 weeks' planned and run miles, the share of key sessions and long runs done, and, after a race, the prediction the app made 8, 4 and 2 weeks before it set against the result. Predictions for each coming A or B race are now saved every week so this is the forecast of the time, not one rebuilt afterwards.
- A note when a marathon build has its long run over half of several weeks, which is how the plan shows that the volume is low for the distance (found on real athletes' histories).
### Changed
- `tools/validate_engine.py --long` runs the planner on every day the file holds before the build; the results are in principle 106.

## 2.10.0-beta.4 - 2026-10-14
### Fixed
- After a dip in running, a build week could be planned 25 to 40% above the best of the last three weeks, because two sessions and a long run, or a marathon-pace long run, have a minimum size. Under 20 miles a week one session now replaces two, and a marathon-pace long run is held back a week when it would cause such a jump. Found by running the planner on 1,500 real athletes' histories from a public dataset; such weeks fell from 3.3% to 0.6% of build weeks.
### Added
- `tools/validate_engine.py` repeats that check, and principles 104 and 105 record the result and its limits.

## 2.10.0-beta.3 - 2026-10-13
### Added
- The marathon assumptions are now checked against 6,582 real marathons from a public dataset of 36,412 athletes (CC BY 4.0). Principles 99 to 103 give what held (weekly volume goes with faster marathons beyond speed; the race equivalence has a median error of 6.4%) and what the data cannot show (long runs separately from volume, taper depth, breaks). The check is `tools/validate_public.py`, not part of the app.

## 2.10.0-beta.2 - 2026-10-13
### Fixed
- The feel and effort rating from your watch was never read: Garmin keeps it in each run's own summary, not in the activity list. It is now fetched for runs of the last four days (checked on your account, where the fields exist).
- The workout files page claimed COROS, Suunto and Polar can import them. That is not confirmed for any of the three, so it now says Garmin watches (USB NewFiles folder) and apps that import FIT workouts.
### Added
- Other training (cycling, swimming and so on) from the last four weeks is listed beside the running load on the Fitness page. It is shown, not counted.
- A note when your weight has fallen 3% or more over eight weeks while a recovery sign is present and you run 15 miles a week or more, suggesting a conversation with a doctor or sports dietitian. A pattern, not a diagnosis.
- Principle 96 names the marathon-pace long run as the durability session, with the research behind it.

## 2.10.0-beta.1 - 2026-10-13
### Added
- Settings is reorganised into five tabs: Training, Watch and data, Weather and maps, Backups and About. A strip at the top shows at a glance whether the watch is connected, whether workouts are being sent, and whether weather and the app password are on. The page is about half as long.
- A bar appears at the bottom when you have changed How you train or Advanced, so "Save and replan" is always in reach. Other switches and choices still save as you set them.
- Yes/No dropdowns are now on/off switches, and the Advanced fields are collapsed behind "Show advanced settings", each saying what Auto will use.
- How a run felt now counts. When your Garmin watch records the feel or effort rating you gave after a run, a last run rated weak (or an effort of 9 or more out of 10) counts as one recovery warning sign, and two such runs in four days count as two. Nothing is typed in; it is read only when the watch has it.
- Training monotony and strain (Foster, 1998) and the week against your last four weeks are shown on the Fitness page. A warning appears only when a week is 20% heavier than your last four and has monotony of 2 or more.
- Heat exposure: with weather on, the Fitness page's race-day forecast says how many of your runs in the last 14 days were in real heat (WBGT 18 or more) and why that matters before a hot race. No pace is changed by it.
- A Monday message (through the daily message address) with last week against its plan and what this week is and why.
- Workout files: the coming days' runs download as .fit workout files in one zip, for watches and apps that import FIT workouts. Nothing is sent anywhere.
- Eight more studies in the research list: Morton and colleagues (1990), Foster (1998), Granero-Gallegos and colleagues (2020), Hoogkamer and colleagues (2018), Casado and colleagues (2022), Fokkema and colleagues (2020), Swain and colleagues (2020) and van Poppel and colleagues (2021). Racinais and colleagues (2015) is now marked as read. New principles 92 to 95 explain each use.

## 2.9.3-beta.16 - 2026-10-13
### Fixed
- Too many workouts could end up on the watch. When Garmin refused to delete an old workout, the app forgot it and sent a new one, leaving two on the day; it now keeps the record and tries again on the next run.
- Lowering "days kept on the watch" left the workouts beyond the new limit on the Garmin calendar. They are now taken off.
- A workout that was uploaded but never scheduled was never removed once its day had nothing planned. It is now deleted.

## 2.9.3-beta.15 - 2026-10-13
### Fixed
- A day's pop-out scrolled back to the top by itself, because the page's automatic refresh redrew it. The refresh now waits while a pop-out is open and catches up when you close it.

## 2.9.3-beta.14 - 2026-10-13
### Changed
- The best time to run is now the first thing in a day's pop-out: a boxed "Best time to run" with the hour in large type, the heat slowdown beside it, then temperature, wind and rain, and one line saying how it was chosen. The detail lines and charts stay below, under "Weather through the day".

## 2.9.3-beta.13 - 2026-10-13
### Fixed
- Dropdowns closed too fast to pick from. The page redraws itself every few seconds (every second while a sync runs), which closed an open dropdown and reset unsaved choices. It now waits while you are using a control (20 seconds after you last touched one) and, on Settings, until your changes are saved. Pressing a button still refreshes at once.

## 2.9.3-beta.12 - 2026-10-13
### Changed
- "Set the hours you can run" in the Weather card, and "Change the hours you can run" in a day's weather pop-out, now jump straight to the hours in Settings and highlight them.

## 2.9.3-beta.11 - 2026-10-13
### Fixed
- The hours you can run now have their own Save hours button directly under them in Settings. Before, they were only saved by "Save and replan" at the bottom of the Advanced card. Saving them does not replan.

## 2.9.3-beta.10 - 2026-10-13
### Changed
- The hours you can run (weekdays and weekends) moved from the Weather card on Connections to Settings, under How you train, and are saved with the Save button there. The Weather card points to it.

## 2.9.3-beta.9 - 2026-10-13
### Changed
- The day pop-out's weather no longer shows the dew point: the temperature chart is a single line, and the dew point is gone from its hover text, summary line and table. It is still used behind the scenes for the heat cost.

## 2.9.3-beta.8 - 2026-10-13
### Changed
- The hourly weather charts in the day pop-out are now three separate panels, each with numbers down the y axis (with faint lines across), every hour of daylight labelled along the bottom, and the unit in its title.

## 2.9.3-beta.7 - 2026-10-13
### Added
- The day pop-out now charts the day's weather by hour across daylight: temperature with dew point, rain (mm an hour, with the chance of rain on hover) and, on days when any hour costs pace, the heat cost (% slower). The best hour is marked and your running window is shaded. Hover or use the arrow keys for values, and open "Hourly figures" for the same numbers as a table.
### Changed
- The forecast sent to the page now carries the hourly figures for the day.

## 2.9.3-beta.6 - 2026-10-13
### Added
- The running window can be set separately for weekends (Saturday and Sunday). Left as "Same as weekdays", the weekday window applies every day, as in beta.5.

## 2.9.3-beta.5 - 2026-10-13
### Added
- Running window (Settings, in the Weather card): the earliest and latest hour you can start a run. The best hour for each day is now chosen inside it as well as inside daylight, and the hour used to ease today's session for heat is held inside it. A day whose window falls wholly in the dark still uses your hours, and says so. Left on "Any hour", nothing changes.

## 2.9.3-beta.4 - 2026-10-13
### Added
- Forecast for each coming day on the plan (when weather tracking is on): the best hour to start, the temperature and dew point then, wind, rain and the chance of rain, sunrise and sunset, and the day's range. Each day in the calendar shows the best hour and temperature (☂ if every daylight hour has rain); click a day for the rest.
- The best hour is chosen between sunrise and an hour before sunset, so it is never in the dark. A dry hour is preferred; then the hour that costs least pace for heat (the same wet-bulb globe temperature model as before); then the one nearest the hour you usually start. Wind and rain are shown only: they change no pace.
- The forecast follows you when you travel: it uses the start of your latest GPS run, so the forecast and best hours move to the new place after your first run there. Times are for that place, including "today" when the best hour has already passed.
### Changed
- The saved forecast now also holds wind, rain, the chance of rain and sunrise and sunset for 16 days, read in the same single request to Open-Meteo, with the same rounded location and nothing else sent.

## 2.9.3-beta.3 - 2026-10-10
### Added
- Recovering: a new entry type next to sick, injured and holiday, for when you are running but not yet well, for example on antibiotics. Sessions become easy running and the long run is shortened to about 60% of its distance (up to 8 miles); nothing is rested and it does not count as a break from training. A second option adds a reminder to keep it flat and slow, for antibiotics that can affect tendons.
- After an illness you recorded, a poor recovery sign eases the day by itself, with no entry needed. For two weeks afterwards, a short night, a heart rate or HRV off your normal, or a resting heart rate 4 or more above it, turns the morning's long run into an easy run of about 60% of its distance (up to 8 miles) and a session into easy running, on the watch too, and says why. The execution score judges that day against the eased run.
### Changed
- The return after sickness is longer: easy running for the days you were out plus two (at least 3, up to 10), instead of the days you were out. Sick entries that touch, such as two days entered separately, now count as one illness, so they get one return instead of two short ones.
- Today's message and the plan show the distance of an eased run, not the distance it replaced.

## 2.9.3-beta.2 - 2026-10-10
### Fixed
- Adding or switching to a nearer goal race (for example a 5K while a marathon was your goal) no longer shows the difference between the two forecasts as a "this week" change. The weekly change now compares a race only with its own earlier forecasts.

## 2.9.3-beta.1 - 2026-10-08
### Changed
- The beta channel now follows the 2.9.3 line, starting from the 2.9.2 release. No functional changes yet.

## 2.9.2 - 2026-10-08
### Added
- Sick, injured and holiday entries can now be edited. Press Edit on an entry to change its type, dates or note (for example, to lengthen or shorten how long you are sick), then Update. The plan replans from today.

## 2.9.1 - 2026-10-05
### Fixed
- iOS: Sessions history table now stacks vertically on iPhone, showing date and stats in a readable 2-column layout.
- iOS: All data tables now stack on mobile instead of requiring horizontal scroll (Race predictor, Last eight weeks, Personal bests, Sessions).
- iOS: Pace-for-heart-rate tag hidden on week bars to prevent wrapping on iPhone.
- The uninstall modal no longer appears on other tabs if you navigate away from Settings before confirming removal.

## 2.9.1-beta.10 - 2026-10-05
### Fixed
- iOS: Race predictor and history tables now stack vertically on iPhone instead of requiring horizontal scroll.
- iOS: Last eight weeks table now displays as a readable 2-column layout on small screens.
- iOS: Personal bests table reorganized for mobile readability.
- iOS: Pace-for-heart-rate tag hidden on week bars to prevent wrapping on iPhone.

## 2.9.1-beta.7 - 2026-10-05
### Fixed
- The uninstall modal no longer appears on other tabs if you navigate away from Settings before confirming removal.

## 2.9.1-beta.6 - 2026-10-04
### Changed
- Phones now get a layout of their own, so the app works both as a desktop page and as a home-screen app. The menu is a bar along the bottom with Plan, History, Fitness, Races, Settings and More (How it works, Change log, Log), always in reach and never wrapping; the top shows only the name, version, last sync time and the Sync button, so the page keeps most of the screen. Desktop and tablet keep the tabs along the top.
- On a phone the plan lists each day as one line (day, session, distance, and a tick for what you ran) instead of a card each, so a week fits on screen. Past days drop their health numbers, which are still in a day's detail. The "drag to swap" hint now reads "Tap a day for detail" on touch screens.
- Lists such as your races and your sick or holiday periods stack neatly instead of squeezing into columns, and form fields share the width evenly.
- The Garmin link on a completed day no longer sits over its distance.

## 2.9.1-beta.5 - 2026-10-04
### Fixed
- The page scrolled sideways in a window about 1000 to 1250 pixels wide (a Mac app window, for example): the header, with the version added, was wider than the window. The header now fits at every width: below 1120 pixels the tabs move to their own row, and above it they tighten.
### Changed
- The version is now a quiet line under the app's name instead of a pill beside it, so the name stays on one line.

## 2.9.1-beta.4 - 2026-10-04
### Fixed
- The Change log page looked broken in 2.9.1-beta.3: the new version pill shared a style name with each version's card, so every card was set in the pill's small monospace type and would not wrap. The pill has its own style now, and the app's name no longer wraps beside it.
### Changed
- The Change log is redesigned: one comfortable reading column, each version with its date and a Running or Beta tag on the left (kept in view while you scroll its entries), and Added, Changed, Removed and Fixed as clear headings with easy-to-read lists. Code names and bold text are shown properly. The six newest versions show first, with a button for the rest. On a phone the version heads each entry.

## 2.9.1-beta.3 - 2026-10-04
### Added
- The version number is always in view: a small pill beside the app's name at the top of every page, amber on a beta. Clicking it opens the Change log.

## 2.9.1-beta.2 - 2026-10-04
### Fixed
- The sync now runs several times a day, as the page says. Before, only the once-a-day sync read your runs; the four-hourly check only repaired the Garmin calendar (and only if sending workouts was on), so "last sync" stayed at the morning's time and a run done later did not show until the next day. Each four-hourly check is now a full sync.
### Added
- Marking one day sick, injured or on holiday: a **Just that day** button beside Save sets Until to the same day as From. The Until box now says what an empty one means (every day is rest until you press Better), which is what removed the rest of the plan from the watch when it was left empty.

## 2.9.1-beta.1 - 2026-10-04
### Added
- Settings, Remove Periodize My Run: removes the app from Mac or Linux after an approval box in which the app password is typed again. It can also delete your data, which has its own tick box. A wrong password counts toward the same five-attempt lock as logging in.
- How it stays safe: the app never runs a command and takes nothing from the request but the password and a yes or no. It only creates one private file that says "keep" or "data". A watcher the installer registers (a launchd agent on Mac, a systemd path unit on Linux) sees the file and runs a fixed script, `uninstall-run.sh`. On Linux that script is a root-owned copy the app cannot change, it ignores anything in the file but those two words, and it deletes only as the app's own user, so nothing the app writes can add a command or point it at another folder.
### Changed
- Installs made before this version need the installer run once more to turn the button on; until then Settings says so. `uninstall.sh` also removes the watcher.

## 2.9.0 - 2026-10-04
### Added
- Release and beta channels for updates. Settings, About, Updates now has an Update channel: **Stable** (the default) offers tested releases only; **Beta** also offers early versions (`2.9.1-beta.1` and so on) that carry fixes before they are released. A beta sorts before its release, so a release always replaces the beta it came from. Installs from before this version ignore beta versions, so only people who choose Beta ever see one.
- Double-click installers inside the project itself: `Install.command` (Mac) and `Install.bat` (Windows), with matching uninstallers, beside the existing `install.sh`.
### Changed
- Installing no longer needs a ready-made package. Download the ZIP of the project from GitHub (Code, Download ZIP) and double-click the installer for your computer. Nothing has to be built for each release, so the packages are no longer published. The README's install section is rewritten to match.
### Removed
- The self-contained Mac app and the Windows and Linux archives that were attached to releases. The Mac installer now does what the other systems do: it downloads Python if the Mac has none, and the libraries.

## 2.8.6 - 2026-10-03
### Changed
- COROS has its own card in Settings, Connections, next to Garmin's, with its sign-in always showing. Before, it could only be found by choosing it in the "Source" list of the "Where your runs come from" card, which showed "Garmin" and sat far down the page, so it looked as if there were no COROS option.

## 2.8.5 - 2026-10-03
### Added
- Setup now asks which watch you use, Garmin or COROS, and signs in to the one you choose. Before, COROS could only be chosen afterwards in Settings. The welcome page and the "building your plan" page no longer assume Garmin.

## 2.8.4 - 2026-10-03
### Fixed
- COROS: the connection now works. Checked against a real COROS account (Europe): sign-in, the list of runs, the .fit download and reading the file all succeed. Two things were wrong. COROS has a separate server for Europe, the USA and China, and a sign-in token works only on its own region's server; the app now tries each and keeps the one that accepts the token. And COROS's list of activities needs a date range, which was not sent.
### Changed
- COROS is no longer labelled experimental. It still uses COROS's unofficial web interface, which COROS can change or block, and it still reads runs only and never sends anything to COROS. The README, disclaimer and Settings say so.
- The message after a failed COROS sign-in now says what to check.

## 2.8.3 - 2026-10-03
### Fixed
- Explain my plan could not be read on a phone in dark mode: the pop-up took the browser's own text colour, black, on the app's near-black background. It now uses the app's colours in both light and dark mode, and a test checks the contrast.
### Changed
- The app is easier to read and use on iPhone and Android: text is larger on phone screens, form fields no longer make iPhone Safari zoom in, buttons and tabs are bigger to tap, and the header takes less room.
- Explain my plan is a sheet that fills the width of a phone, with its Close button always in view while you scroll, and the page behind it no longer scrolls.
- Pop-ups (a day's detail, pacing plan, trends) fill the phone screen and keep clear of the home bar.
- The tab strip scrolls to show the tab you are on, and the app keeps clear of the notch and the home bar when opened from the home screen.
- The home-screen app's icon, colours and name are declared more completely (separate maskable icon, dark start-up colour), so Android installs it properly.
### Added
- Step-by-step instructions in the README for putting the app on an iPhone or Android home screen.

## 2.8.2 - 2026-10-03
### Added
- Ready-made packages for Mac, Windows and Linux (including Raspberry Pi) can now be downloaded from the project's GitHub releases page, with a `SHA256SUMS.txt` to check them against. The README's install section starts with them; installing from the source files is still described below that.

## 2.8.1 - 2026-10-03
### Changed
- The README now shows the app in pictures: the plan, the weeks ahead and the season, a day's card, Explain my plan, the Fitness page, a run in detail, a pacing plan and the phone view. All are taken from the app running with a made-up test athlete, by `tools/screenshots.py`.
### Removed
- The PDF brochure and the tool that built it. The README's pictures replace it.

## 2.8.0 - 2026-10-03
### Added
- Installers no longer need Python to be installed first. If the computer has no Python 3.12 or later, the installer downloads a private copy into the app's own folder (about 30 MB, checked against a pinned SHA-256 in `runtime.lock`; a download that does not match is refused). Nothing is installed system-wide, and the uninstaller removes it. Works on Windows (64-bit), Linux (x86-64 and 64-bit ARM) and Apple-silicon Macs.
- Packages to send to someone, built by `tools/package.py`: a self-contained Mac app ("Periodize My Run.app", Apple silicon, holding its own Python and every library, so nothing is downloaded), and small Windows and Linux archives with a double-click installer that downloads what the computer lacks.
- An uninstaller for every system: `./uninstall.sh` on macOS and Linux, `uninstall.ps1` on Windows. It stops the app, stops it starting by itself and removes its Python environment. Your data is kept unless you add `--data` (Windows: `-Data`), which asks you to type "delete" first.
### Changed
- Links in the app and its documents now point to the project's GitHub address, `romahony26/periodize-my-run`, the same one the in-app update check uses. Before, the links and the update check named different addresses, so the update check could never find a new version.
- The README's install section is rewritten as numbered steps for macOS, Windows and Linux (including Raspberry Pi), with where to get the files, where things are kept on each system, and a new Uninstall section. Both installers now end by saying how to remove the app.
- The README's feature list now covers weather, Explain my plan, the purpose of each run and what is learned from your own history.

## 2.7.4 - 2026-10-03
### Added
- The History tab shows the trend of your execution score over time: a line of the average of your last five scored sessions, session by session, with each session's own score on hover. It appears once three sessions have been scored, so it no longer waits for a second full week. The weekly bars are still shown once there are two weeks.

## 2.7.3 - 2026-10-03
### Fixed
- The History tab did not show today's run until the next day: it only listed days before today. A run now appears there, scored, as soon as it has been synced. A day whose run has not been done yet is still not counted as missed.
- The History tab kept showing what it had loaded when the app was first opened. It now reloads after every sync, whether or not the tab is open at the time.

## 2.7.2 - 2026-10-03
### Changed
- The "Is it working?" checks now allow for the weather on the day, when weather is switched on. Each aerobic test shows its weather, and its paces are what they were worth in neutral weather, so a test in July compares fairly with one in January. The prediction check takes what the weather cost off each race time before comparing it with the prediction (marked ☀). Long runs done in warm conditions (above 18 °C WBGT) are left out of the durability trend, because heat raises heart-rate drift by itself. The monthly pace at a heart rate was already adjusted in 2.7.0; its note now says so.

## 2.7.1 - 2026-10-03
### Changed
- "The research behind the plan" is now at the bottom of the How it works page, after the explanation of what the app does.

## 2.7.0 - 2026-10-03
### Added
- Weather for every run. With weather switched on (Settings, Connections), each outdoor run of the last three years is given the temperature, dew point, wind and rain it was run in, read once from Open-Meteo for the run's rounded start location and hour. It is shown with the run on its day card.
- Fitness is judged on what a run was worth in neutral weather. A run's pace is scaled for the heat (or the cold) before it counts as evidence of your threshold, your pace at a heart rate, or your time at threshold and race pace, so a hot spell is not read as lost fitness. The reason given for your threshold says when the weather was allowed for.
- Principles: a new section 16, "Weather", covering heat, cold, wind and rain, with seven added references.
### Changed
- How much heat slows you now comes from race data, not a coaching table: performance is best at a wet-bulb globe temperature of 7.5 to 15 °C and falls about 0.35% for each degree outside it (1,258 endurance races). Fast paces are eased by that amount on hot days, and a day at 28 °C or more turns the session into an easy run. The estimate is for shade, so on humid days it eases a little less than the old table did (about 2.3% at 25 °C with an 18 °C dew point, where the table gave 3.75%).
- Wind and rain are recorded and shown but change no figure: in marathon results they had no effect of their own once temperature was allowed for.
- "Heat adjustment" in Settings is now "Weather". It is still off unless you switch it on. When on, the rough locations (to about 10 km) and dates of your runs are sent to Open-Meteo, where before only your latest rough location was.

## 2.6.1 - 2026-10-03
### Fixed
- The lists of studies on the How it works page closed by themselves a few seconds after being opened, because the page refreshes every six seconds. An open list now stays open, and the refresh waits while any expandable section is open (this also fixes "Enter a test by hand" on the Fitness page).

## 2.6.0 - 2026-10-03
### Added
- Explain my plan. A button on the plan page opens a panel that lists every decision shaping your plan: what you are building toward, your peak week, how fast the miles build, the long run, how many hard sessions and which kinds, your taper, down weeks, day-to-day tuning, and what stands between you and your goal. Each one shows the decision, the numbers from your own data that led to it, and where the rule comes from: a named study, a coaching convention, or this project's own choice.
- What each run is for. Every planned day now says its purpose in a sentence or two, including rest days and a session that was changed to an easy run.
- Your own response, learned from your whole history, with nothing to enter. Your taper: for each past race of 15 km or more, how deeply the last week was cut is set against how close the race was to your best level of the time; with six or more races and a clear pattern the taper moves 5 points deeper or lighter, inside the range the research supports. Miles or hard running: across the eight-week blocks in your history, the change in your watch's fitness estimate is compared with the miles and hard runs in each; if miles clearly matter more, every other week before the race-specific phase has one hard session, not two, at the same distance. Both show their sample size and say "not clear" unless the pattern is strong.
- What stands between you and your goal: whether the gap to your goal time is mostly speed or mostly endurance, and which part of your endurance is furthest from full.
- The research behind the plan, on the How it works page: every peer-reviewed study used, with the principles that rely on it, and separately the few sources that are not peer-reviewed. Only findings are used; no text, tables or figures are copied.
- Principles: a new section 15 (individual response, taper, what decides a marathon time and why runners stall, purpose and explanation), and a principle on what a watch can and cannot measure about sleep.
### Fixed
- The message shown after pressing Sync said "Updating from Garmin"; it now says "Syncing".

## 2.5.0 - 2026-10-03
### Changed
- Your peak week now comes from what you have held without breaking down, not from your recent average. It is taken from your best eight-week block that was followed by six sound weeks (no two weeks in a row under 35% of the block, and no time recorded as sick or injured; rest after a race, a very long run or a holiday does not count against it): the larger of that block from all your history and 110% of that block from the last three years. A high recent average no longer raises it. With too little history, the old rule (your last eight weeks plus 25%) still applies.
- Volume builds more slowly on new ground. Up to the most you have held for eight weeks in the last year, a building week still rises by 6%; beyond that it rises by 3%. After a week or more without running, the distance is held level for three weeks before building again. The reasons shown with each week say which applied.
- Long races for men: the race note now presses the patient start harder, because men slow far more than women in the second half.
### Added
- "When you run" on the Fitness page: your usual start time and the share of runs in the morning, daytime and evening. When there is enough data it also shows how you slept after hard runs that ended within four hours of sleep compared with your other runs, counts early runs that followed a short night, and reports when your usual run time has shifted by an hour or more (as a pattern only). Nothing here changes the plan and nothing has to be entered.
- A watch-out on the morning after a hard run that ended within four hours of sleep, because that morning's heart-rate variability will read low for a reason other than fatigue.
- For women, a warning about a jump in run length now also says what a bone stress injury feels like, since these are about twice as common in women.
- The time you fell asleep is now kept from the Garmin sleep data already fetched. The first sync after this version reads it for the nights already stored.
- Your history now shows the most you have held without breaking down (three years, and ever) and how many weeks you have gone without a week off running.
- Principles: a new section 14, "Consistency, working life and sex", with the peer-reviewed sources for all of the above, and what the evidence does not support (planning by menstrual cycle phase; reading a shift in run time as stress).

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
