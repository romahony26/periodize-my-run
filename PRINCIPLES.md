# Running principles

The training principles Periodize My Run is built on, written in the project's own words.

This document holds ideas, findings and rules, not anyone's text, tables or training schedules. Each principle says what the
planner actually does and why. Where the reason is published research, the study is named so it can be checked. Where it is a
coaching convention, or a choice this project made, it says so. Where Periodize My Run does not yet do what the evidence suggests, the
last section says that too. Nothing here is medical advice.

## How to read the marks

Every principle carries one mark:

- **[R]** rests on peer-reviewed research. The strength follows in brackets:
  - *strong*: a meta-analysis, a consensus statement, or several trials that agree;
  - *moderate*: a single trial, or a large observational dataset (which shows association, not cause);
  - *limited*: small, short or indirect studies, or a population unlike most runners.
- **[C]** a widely used coaching convention, supported by practice rather than controlled studies.
- **[P]** this project's own choice of a value or a rule, made because something had to be chosen.

Most of the research was done on trained recreational and sub-elite runners, over 6 to 16 weeks, with 10K or laboratory tests
rather than marathons. The evidence is thinnest at the two ends: 5K and 10K training rests on a handful of small trials, and
ultramarathons and mountain races have almost no training trials at all, so sections 11 and 12 lean more on laboratory studies,
race data and coaching practice, and say so. Women and older runners are under-represented. Averages hide wide individual
differences in almost every finding. That is why Periodize My Run keeps measuring the athlete against their own history.

## How the references are checked

`tools/check_references.py` reads this file and checks it against itself: every principle carries a mark, every principle marked **[R]**
names a study, every study named in a principle is in the reference list, and every study in the list is named. With `--live` it looks
each article up in Europe PMC (and Crossref for journals PubMed does not index) and compares title, first author and year. Entries
marked *From memory* are the four no index holds (a book chapter, a South African journal, a meteorology journal and a regulator's
notice); the others were matched to their published record. This is how the 2022 respiratory-illness citation was found to name the wrong paper.

## 1. Foundations

1. **Consistency beats any single session.** [R] (*moderate*) Over five years of elite athletes, those who completed most of
   their planned training weeks were several times more likely to reach their performance goals than those who lost weeks to
   injury or illness (Raysmith and Drew, 2016). Every rule below leans toward the plan you can complete. When in doubt, do less.
2. **Your own history is the yardstick.** [R] (*strong*) Sleep need, heart-rate variability, resting heart rate and the load a
   body tolerates differ widely between people (Walsh and colleagues, 2021; Plews and colleagues, 2013). Periodize My Run judges each
   reading against your own recent normal, never against a population table.
3. **Trends, not single days.** [R] (*strong*) One night's heart-rate variability or one slow run is mostly noise. Periodize My Run acts
   on averages over days and weeks (Plews and colleagues, 2012, 2013).
4. **No single warning sign decides.** [R] (*strong*) Overreaching and overtraining have no single reliable marker; they are
   recognised when several signs agree and other causes are ruled out (Meeusen and colleagues, 2013). Sleep, HRV and resting heart rate
   move together and are noisy, so a recovery week needs two warning signs in two weeks running (or three at once); two signs in a single
   week only hold the volume level. Easy pace at a heart rate is shown but is not a warning sign, because heat, wind, hills and watch error
   move it by a few per cent. [P]
5. **Pain and illness override the plan.** [C] A planner cannot examine you. Pain that changes your stride or builds during a
   run, or illness with fever or chest symptoms, means stop and see a clinician.

## 2. What decides how fast you race

6. **Three things set distance-running performance: how much oxygen you can use, how large a share of it you can sustain, and
   how economically you run.** [R] (*strong*) Training moves all three, at different rates (Joyner and Coyle, 2008; Bassett and
   Howley, 2000).
7. **A fourth: how well you hold them when tired.** [R] (*moderate*) Runners differ in how much their economy and sustainable
   pace fade late in a long race. This "durability" predicts marathon performance on top of the other three (Jones, 2024), and
   heart rate drifting up at a steady pace is a usable field sign of it (Smyth and colleagues, 2022).
8. **Threshold pace is the most useful single number.** [C] It is roughly the pace you could hold for an hour. Training paces
   are set as fractions of it, and it tracks race performance from 10K to the marathon.
9. **Fitness is read from what you actually ran, not from your goal.** [P] The threshold estimate comes from recent race
   results, your own pace-to-heart-rate relationship over the last four weeks, and the watch's own estimate while it is less than
   six weeks old. A goal time only shows the gap.
10. **Fitness estimates move slowly, except during a break.** [P] The estimate may rise by at most 1.5% a week and fall by at most
    0.5%, so one good or bad run cannot swing the plan. When you stop running, though, fitness really does fall: trained runners
    lose roughly 4 to 14% of their aerobic capacity over two to four weeks without training, recent gains first (Mujika and
    Padilla, 2000) [R] (*moderate*). So after 10 days without a run the estimate eases by 0.35% a day, up to 12%, and your first
    paces back are set from that. [P]
11. **Longer races need endurance on top of speed.** [R] (*strong* for the association) Across 85 studies, weekly distance, the
    number of long runs and total hours were the most consistent training predictors of marathon time (Doherty and colleagues,
    2020). Simple formulas that scale a short race to a marathon are optimistic for recreational runners who lack that volume
    (Vickers and Vertosick, 2016). Periodize My Run slows a marathon prediction by up to 5% until the long runs, weekly volume and
    race-pace running are in place. [P]

## 3. How hard, and how often

12. **Most running is easy.** [R] (*strong* that it is mostly easy; *moderate* for the exact share) Successful endurance
    athletes do roughly four fifths of their training at low intensity (Seiler and Kjerland, 2006; Haugen and colleagues, 2022).
13. **For the marathon, the hard fifth is mostly moderate.** [R] (*moderate*) Marathon runners at every level train with a
    "pyramid": lots of easy running, a fair amount around threshold and marathon pace, and a little very fast running (Haugen and
    colleagues, 2022; Muniz-Pumares and colleagues, 2024). A strictly "polarised" pattern, all easy or very hard, improved some
    laboratory measures in short trials (Stöggl and Sperlich, 2014) but has not been shown to give better race results (Silva
    Oliveira and colleagues, 2024). A systematic review of highly trained and elite distance runners found the same pyramid, with
    marathoners leaning further that way than 1500 m runners (Casado and colleagues, 2022) (*moderate*).
14. **Easy means easy.** [R] (*moderate*) The best-documented training error is running easy days harder than intended and hard
    days easier (Foster and colleagues, 2001). Periodize My Run scores every run on how closely it matched the planned mix of easy,
    moderate and hard minutes. [P]
15. **Hard days are separated by easy days.** [C] No two hard days run back to back, and the long run counts as a hard day.
16. **A week holds one long run and one or two sessions.** [C] Two sessions when you run five or more days, one otherwise. The
    rest is easy running or rest.
17. **One new stress at a time.** [C] When fast running is being reintroduced, weekly volume is held level that week.
18. **A missed session is moved only if it fits.** [P] It goes to a later day that keeps hard days apart. If none exists it is
    dropped: squeezing sessions together costs more than the session gains.

## 4. Building volume, and avoiding injury

19. **Volume is built before intensity, and general work before race-specific work.** [R] (*moderate*) This is how world-class
    distance runners organise a season (Haugen and colleagues, 2022), and how Norwegian world-class coaches describe best practice
    (Sandbakk and colleagues, 2025).
20. **Volume rises gently; recovery signs can hold the build but never speed it.** [P] In a building week, distance rises by up to
    about 6% on your recent level, as far as the most you have held for eight weeks in the last year; beyond that the step is half,
    about 3%, until you have run at least 95% of the planned miles in each of the last three weeks, which earns the full 6% again
    (consistency first: principle 1, and Feely and colleagues, 2022). A week with a warning flag, or with both HRV and resting heart rate more than one spread off your own normal, is held
    level. Steady readings change nothing: HRV-guided trials used the readings to pull intensity back, not to add volume, the pooled
    benefit was small and not significant (Manresa-Rocamora and colleagues, 2021), and watch HRV and resting heart rate are not accurate
    enough to give a green light. The 6%, the 3%, the 20% limit, a down week every third week and the build starting from your best
    three-week average of the last six are conventions: no study tests them. Before the race-specific phase the volume stops at 90% of
    your peak.
21. **The old "10% a week" rule is not what prevents injury.** [R] (*strong*) In a randomised trial, a gentler weekly build did
    not reduce injuries in new runners (Buist and colleagues, 2008), and the ratio of this week's load to the last month's has conceptual and statistical problems and is not supported as a way to prevent
    injury (Impellizzeri and colleagues, 2020; the project's 20% limit is a convention, not this ratio). Large jumps are another matter: more than about 30% over two
    weeks showed only a non-significant trend towards distance-related injuries in novices (Nielsen and colleagues, 2014), and runners preparing for a half marathon who raised a
    week by 20% to 60% had more injuries in the following three weeks, but not later, than those who raised it by less than 20% (Damsted and
    colleagues, 2019). Periodize My Run's 6%, or 3% on new ground, stays well clear of both, and no build week is planned more than 20% above the best of
    the last three (principle 104).
22. **What matters most is the single longest run.** [R] (*moderate*) In a study of over 5,000 runners, a run more than 10% longer
    than the longest of the previous 30 days was linked with more overuse injuries, while week-to-week mileage change was not
    (Frandsen and colleagues, 2025). Periodize My Run never plans a long run more than 10% beyond your longest in the
    last 30 days. Among recreational marathon and half-marathon runners, high weekly volume and long endurance runs went with faster finishes and
    were not related to more injuries (Fokkema and colleagues, 2020) (*limited*: questionnaires, not a trial).
23. **Your limits come from what you have held without breaking down, not from your recent average.** [P] The peak week is
    taken from your best eight-week block that was followed by six sound weeks: no two weeks in a row under 35% of the block,
    and no time recorded as sick or injured. Rest after a race, a very long run or a holiday does not count against a block. The
    peak is the larger of that block from all your history and 110% of that block from the last three years, up to 90 miles. A block that ended more than three years ago counts less and less, and is gone eight years after it ended, because the tissue tolerance behind it is not kept for ever (no study says how fast it goes). [P] A
    high recent average no longer raises it, and a block too recent to have six weeks after it is not yet counted. With too
    little history for any such block, the peak is your recent eight weeks plus 25%. Long-run length scales from the peak and
    from your goal distance. No study has tested this rule directly; it follows from the finding that previous injury, not
    weekly mileage change, is the strongest predictor of the next injury (principle 24), and from the idea that tissue tolerates
    what it has already been trained to carry (Damsted and colleagues, 2019, tested whether the schedule a runner had been
    following changes the tolerable jump, and found no clear effect) (*limited*).
24. **Previous injury is the strongest known risk factor for the next one.** [R] (*strong*) (Saragiotto and colleagues, 2014;
    van der Worp and colleagues, 2015; Hulme and colleagues, 2017; van Poppel and colleagues, 2021) In a year-long study of recreational runners, a history of
    injury roughly doubled the injury rate, while weekly distance, age and sex showed no clear link (Desai and colleagues, 2021). After an injury Periodize My Run returns you on easy running for twice as long as you were out,
    up to 14 days. [P]
25. **After any break, build back gradually.** [C] Two or more weeks well below your usual level, whatever the reason, are followed
    by a return lasting about as long as the break (up to four weeks): about half your usual volume first, then three quarters,
    all easy. Periodize My Run notices the break from your runs; nothing has to be entered.
26. **Everyday walking is load too.** [P] Unusually heavy weeks on your feet count as a warning sign for the weekly plan.

## 5. The sessions

27. **Threshold running** raises the pace you can sustain. [R] (*limited*) It is done as repeats with short recoveries, run in
    control rather than to exhaustion. World-class runners and coaches describe this controlled, broken-up threshold work as
    central (Casado and colleagues, 2023; Tønnessen and colleagues, 2024), and more total work at slightly lower intensity
    beat less work at higher intensity in a controlled trial (Seiler and colleagues, 2013). Periodize My Run progresses it by adding
    time at the pace, from 15 to 40 minutes, before the pace itself moves. [C]
28. **Faster repeats** (around 10K and 5K pace) develop maximal aerobic capacity. [R] (*moderate*) Well-trained runners need
    high intensities to raise it further (Midgley and colleagues, 2006). For a 5K or 10K goal they are the main session; for a
    marathon they appear about one week in three once threshold work is established. [P]
29. **Race-pace running becomes the centre of the final phase before a long race.** [R] (*limited*) World-class marathoners shift
    from faster intervals early in the season to marathon-pace work late (Haugen and colleagues, 2022). For the marathon,
    Periodize My Run builds midweek marathon-pace runs (4 to 8 miles) and, every second week or so, a long run with 8 to 14 miles at
    marathon pace. [C]
30. **Long runs are steady, not shuffled.** [C] Once fast running is established, the long run is run at a steady effort a
    little slower than marathon pace; early on, and for ultra goals, it is easy. Except for ultra goals, a long run is kept to
    about three hours: beyond that, the injury risk and recovery cost grow faster than the benefit. [C]
31. **Aerobic runs by heart rate.** [C] Before the race-specific phase, one run a week holds a fixed heart rate below threshold
    and lets the pace float. The heart rate moves up 5 beats only when 10 miles at the current level is comfortable. [P]
32. **Short fast strides and 200 m repeats** keep speed and form without heavy fatigue. [C]
33. **Strength training improves running economy without harming aerobic fitness.** [R] (*strong*) Heavy-load and plyometric
    training work best; light-load and isometric training much less (Llanos-Lagos and colleagues, 2024). Explosive training cut 5K
    times by about 3% in nine weeks (Paavolainen and colleagues, 1999) (*moderate*), and one trial found strength work made economy
    hold up better late in a long run (Zanini and colleagues, 2025) (*limited*). Periodize My Run places two short sessions a week on easy
    days, one heavy and one with plyometrics (hops, skips, bounds); one a week in the race-specific phase; none in the last two
    weeks before the goal race. [C]

### When a day is lost: how the week is rebuilt

These are the rules the planner follows when a trip, holiday or illness takes a day out of a week. They are coaching convention and
this project's own choices, not findings from trials. [C] [P]

- **Hard days are kept apart.** (A convention: a quality session the day before a long run is a legitimate marathon layout in some programmes, and nothing tests the spacing. The planner avoids it by default; you can still move days by hand.) A quality session, the long run and a race each have an easy or rest day on either side. If a change
  would put two together, the quality session becomes an easy run; the long run and the race never move for it. [C]
- **The long run is the last session to go.** If its day is spent away, it moves to a day at home in the same week: the other
  weekend day first, then the nearest day, the day before first. [P]
- **The week keeps its shape.** When the long run moves to the day before, the rest day goes and the days from it to the long run each
  move a day earlier, so both quality sessions survive and the rest day lands on the day away. With no rest day to give up, the long
  run swaps with an easy day and any quality session beside it is eased. [P]
- **Days of illness or injury are never used** for a moved session. [P]
- **A week with four or more days away is the down week.** The trip trims the runs, so it counts as the lighter week, restarts the count of
  build weeks, and the week after goes back to building where you left off: no second down week and no return week. A few days of lighter
  running cost very little fitness: in the one small study of complete rest found for this project, two weeks cost about 3 ml/kg/min of VO2max
  and left running economy unchanged (read as an abstract only, so it is not cited here). Longer breaks keep the return rules. [P]
- **A week that is away from start to finish** has no long run to place: every run is short, easy and optional. [P]

### Goal-driven volume, and the midweek medium-long run

- **A marathon goal time sets how much volume the plan may build toward.** [C] Across marathoners, more weekly distance goes with faster
  times (Doherty and colleagues, 2020; Fokkema and colleagues, 2020), and the project's own check of 6,582 marathons found 5 to 7% faster per
  standard deviation (principle 99). No study gives a mileage for a time. The rule of thumb used is 55 miles a week for 3:00, a mile more for each
  minute faster (65 for 2:50), within 40 and 90. The ceiling rises toward it but never past half again on the most you have held in the last
  three years; the weekly step is still 6%, or 3% past what you have held, and a warning sign holds it. [C] [P]
- **A marathon, half-marathon or ultra build has a midweek medium-long run** (about a quarter of the week, 8 to 14 miles, easy with a steady
  finish), alternating with the heart-rate aerobic run. It adds the aerobic miles that marathon endurance needs without a third hard
  session. [C]
- **More than one goal race is flagged.** Training can peak for one race at a time, so the plan says so and the Races page notes it. [C]

## 6. The shape of a season

34. **Load rises in steps, with lighter weeks.** [C] After three full weeks, the next is a down week at about three quarters of
    the volume. From age 50 (read from your Garmin profile) it comes after two full weeks instead: endurance performance declines
    with age (Tanaka and Seals, 2008) [R] (*moderate*), and older runners are widely held to need longer recovery between hard
    blocks [C].
35. **No periodisation model is proven best.** [R] (*moderate*) Successful elite systems differ sharply, and trials have not shown
    one structure to be superior (Grivas and colleagues, 2026; Mølmen and colleagues, 2019). Periodize My Run uses a simple build, down,
    specific and taper sequence, and adapts it to what you actually do. [P]
36. **Taper by cutting volume, not intensity.** [R] (*strong*) Reducing volume by roughly 40 to 60% while keeping some fast running
    and the usual number of runs improves performance (Bosquet and colleagues, 2007; Wang and colleagues, 2023). Among 158,000
    recreational marathoners, a disciplined three-week taper was linked with finishing about 2.6% faster than a minimal one (Smyth
    and Lawlor, 2021) (*moderate*). Periodize My Run tapers over three weeks for the marathon and ultra (about 80%, then 65%, then race
    week) and two weeks for the half (65%, then race week). For 5K and 10K, the week before race week drops to about 70%, keeping
    a short session: about 8 to 14 days in all, the range the meta-analysis found best. Taper length for ultras has never been
    tested; the marathon taper is borrowed.
37. **A race is followed by recovery.** [R] (*limited*) Easy running from two days after a marathon did not slow recovery
    compared with rest (Martínez-Navarro and colleagues, 2021). Periodize My Run plans a recovery week at about half your usual volume
    after a race or a very long run, with no sessions. [C]

## 7. Is it working?

38. **Faster at the same heart rate is the sign of aerobic progress.** [C] Periodize My Run tracks your pace at fixed heart rates month by
    month, and offers a stepped heart-rate test about every month.
39. **Aerobic change is slow.** [C] Expect little after three weeks and clear change after six. Testing more often measures noise.
40. **Hills are converted to their flat equivalent.** [R] (*strong*) The energy cost of running on a gradient has been measured
    (Minetti and colleagues, 2002), and is used to compare hilly and flat runs.
41. **Predictions are checked against your races.** [P] For each race in the last three years, the prediction is rebuilt from what
    was known the Monday before and set against your actual time, so you can see how far to trust it and whether it leans fast or
    slow for you.
42. **Weeks are compared, not single runs.** [P] One run's pace for its heart rate swings with wind, heat, route and time of day.
    With weather switched on, the day's weather is allowed for in each of these checks (principle 89): the monthly pace at a
    heart rate and each aerobic test are shown as what they were worth in neutral weather, a race is set against its prediction
    after taking off what the weather cost, and long runs done in warm conditions (above 18 °C WBGT) are left out of the
    durability trend, because heat raises heart-rate drift by itself (Wingo and colleagues, 2012). Wind is not allowed for.
43. **Fitness is three things, each with its own trend.** [R] (*moderate*) Speed (the threshold estimate) mostly decides 5K and
    10K; the endurance base (long runs, race-pace miles, weekly volume) matters more as the race gets longer; durability (how well
    pace holds against heart rate late in long runs) matters most for the marathon and longer. How much threshold speed falls
    after prolonged running predicts marathon time (Hunter and Muniz-Pumares, 2025). Periodize My Run shows each over the window that
    suits it: speed over 6 weeks, steady within 1%; the endurance base over 4 weeks; durability over the last six long runs;
    heart-rate variability, resting heart rate, sleep and steps as 7-day averages against your 60-day normal. The windows follow
    the research; the steady bands are this project's choice. [P]
44. **Race times should spread predictably with distance.** [R] (*moderate*) Across world records and good runners, doubling the
    distance takes a little more than twice as long (Riegel, 1981): pace slows by about 4% each time the distance doubles, about
    15 seconds a mile at 6-minute pace. A much wider spread means endurance, not speed, is what limits you.
45. **Aerobic drift.** [R] (*moderate*) On a long steady run, how far your pace per heartbeat fades in the second half is a sign
    of durability (Smyth and colleagues, 2022). Under 5% is a common rule of thumb. [C]

## 8. Training load

46. **Load is minutes weighted by intensity.** [R] (*moderate*) Easy, moderate and hard minutes count 1, 2 and 3 (Lucia and
    colleagues, 2003).
47. **Fitness and fatigue are both responses to load, on different time scales.** [R] (*moderate* as a concept) Fitness builds and
    fades over weeks, fatigue over days; "form" is the difference (Banister, 1991; Morton and colleagues, 1990). The model fits past data well but predicts an
    individual's future performance poorly (Hellard and colleagues, 2006), so Periodize My Run shows it as a guide and never plans from
    it. The 42-day and 7-day time constants are convention. [C]
48. **Execution is measured against the plan.** [P] A run is scored on how far its easy, moderate and hard minutes departed from
    the session set. Too much counts the same as too little.

## 9. Recovery and readiness

49. **Sleep matters from a single night.** [R] (*strong*) One short night measurably reduces endurance performance the next day,
    mostly through how hard the effort feels (Lopes and colleagues, 2023; Craven and colleagues, 2022). Periodize My Run reads last night
    on its own, and the last three nights together because sleep debt builds.
50. **Heart-rate variability and resting heart rate are read as weekly trends.** [R] (*moderate*) A single reading is noisy. A
    7-day average against your own normal range is the established method, and a shift of about half your normal spread is the
    smallest change treated as real (Plews and colleagues, 2012, 2013). In the one validation study read for this project, a Garmin
    watch's overnight HRV agreed least well with a chest-strap reference of the five devices tested (about 10% error), and its resting
    heart rate could not be checked at all (Dial and colleagues, 2025) (*limited*). So the readings are used to hold the build back and to
    colour the day, never as a green light.
51. **Expect small gains from readiness-based adjustment, not miracles.** [R] (*strong*) Training guided by heart-rate variability
    gave small, non-significant average gains over a fixed plan in the pooled trials, with some sign of fewer non-responders; the gain came
    mostly from doing fewer hard sessions (Düking and colleagues, 2021; Manresa-Rocamora and colleagues, 2021; Granero-Gallegos and
    colleagues, 2020).
52. **Poor recovery eases the fast running, not the easy running.** [P] Each warning sign slows the day's fast paces by a small
    fixed amount (about 1.2% to start, then learned from your own runs), up to four signs.
53. **When the signs persist or pile up, the session becomes an easy run.** [R] (*moderate*) In the trials of readiness-guided
    training, a hard day was swapped for an easy one when the morning signs were poor, rather than only slowed (Düking and
    colleagues, 2021). Periodize My Run does this automatically on a morning with three or more warning signs, or when a sign has lasted
    three mornings in a row; the watch gets the easy run, and the planned session is still shown. [P]
54. **Illness means rest, then a gradual return.** [C] While sick, no running. Afterwards, easy running for as many days as you
    were out plus two (at least three, up to ten), building from half distance. Two entries that touch are one illness. The return
    is longer than the time out because symptoms of an acute respiratory illness last about a week on average in athletes
    (7.1 days, 95% interval 6.2 to 8.0, across 54 studies and 31,065 athletes: Snyders and colleagues, 2022), and the graded return-to-exercise templates, written for COVID-19 and not validated for other
    illnesses, run to about a week or more of easy steps before full training (Elliott and colleagues, 2020). No study tests the
    exact length; the numbers are this project's choice. [P]
54a. **For two weeks after an illness, a poor recovery sign eases the long run and the sessions.** [P] The "neck check" used to
    decide whether to run while ill rests on a weak scientific basis (Hull and colleagues, 2020), and only 4 of the 54 studies in
    a review reported days until return to sport after a respiratory illness (Snyders and colleagues, 2022). On a morning in the two weeks after an illness you recorded, any readiness warning
    sign, or a resting heart rate 4 or more above your own normal, turns a long run into an easy run of about 60% of its distance
    (up to 8 miles) and a session into easy running, and says why. This borrows the rule that readiness-guided training swapped hard
    days for easy ones when morning signs were poor (Düking and colleagues, 2021), and applies it with a lower threshold because
    the cost of a relapse is larger than the cost of a gentle day. The threshold is not from a study.
54b. **While on treatment you can choose easy running only.** [P] Marking yourself as recovering turns sessions into easy
    running and shortens the long run, with nothing rested. The fluoroquinolone antibiotics carry a regulator's boxed warning for
    tendinitis and tendon rupture (U.S. Food and Drug Administration, 2008), so that option also asks for flat, slow running and
    no hills. It does not know which antibiotic you take; it only acts on what you choose.

## 10. Racing

55. **Even effort is the fastest way to cover a course.** [R] (*moderate*) Recreational marathoners who start faster than they can
    sustain are the ones who "hit the wall" (Smyth, 2021), and runners with more experience and higher weekly volume slowed least in the second half (Swain and colleagues, 2020) (*limited*). Periodize My Run gives a starting pace and asks for no faster in the first
    half. On a hilly course, even effort means slower uphill and faster downhill: a course file gives an even-effort split for
    every mile. [C]
56. **Fuel long efforts.** [R] (*strong*) About 30 to 60 g of carbohydrate an hour for efforts of 1 to 2.5 hours, and up to 90 g
    beyond that, using mixed sugars (Thomas and colleagues, 2016; Jeukendrup, 2014).
57. **Practise fuelling in training.** [R] (*moderate*) The gut adapts to taking carbohydrate on the run (Costa and colleagues,
    2017). Periodize My Run steps up the long-run fuelling target from 30 to 70 g an hour over the months before the race. [P]
58. **Race week follows the evidence, worked out for you.** [R] (*strong*) Before a marathon or longer, about 10 g of carbohydrate
    per kg of body weight a day for the last two days (Thomas and colleagues, 2016), with the amount worked out from your Garmin
    weight. On race day: caffeine at about 3 mg per kg improves endurance by a few per cent (Southward and colleagues, 2018), but
    only if you have tried it in training; drink to thirst, because drinking too much is the serious risk for most runners
    (Hew-Butler and colleagues, 2015); no ibuprofen or similar painkillers, which were linked with more serious problems during
    marathons (Küster and colleagues, 2013) (*moderate*); and race in shoes you have already run in at race pace. Racing shoes with a stiff plate and soft foam cut the energy cost of running by about 4% in 18 high-calibre runners (Hoogkamer and colleagues, 2018) (*moderate*), which is a reason to choose them and a stronger reason to run in them first. [C]
59. **Heat slows you; plan for it.** [R] (*strong*) Across 1,258 endurance races, performance was best at a wet-bulb globe
    temperature (WBGT, which combines temperature, humidity, sun and wind) of 7.5 to 15 °C, about 10 to 17.5 °C of air
    temperature, and fell by 0.3 to 0.4% for each degree outside that range (Mantzios and colleagues, 2022). Marathon times
    fall progressively as it gets warmer, and slower runners lose proportionally more (Ely and colleagues, 2007; El Helou and
    colleagues, 2012). If you switch weather on, fast paces are eased by 0.35% for each degree of WBGT above 15 °C, a day at
    28 °C WBGT or more turns the session into an easy run [C], and the race-day forecast for your goal race is shown once it is
    within 16 days. WBGT is estimated for shade from temperature and humidity (Stull, 2011), so full sun on a still day is
    harder than the figure says. Off by default, because it needs a weather service (Open-Meteo), which receives only rough
    locations and dates. [P]
60. **Hilly races need hilly training.** [C] Weekly climb is raised toward the race's climb per mile over the final months.
61. **Race results are compared across ages with age grading.** [R] (*moderate*) Performance declines with age at a known average
    rate (Tanaka and Seals, 2008); standards by age, sex and distance come from public-domain tables (Jones, 2025).

## 11. 5K and 10K

62. **The easy share stays high for short races too.** [R] (*moderate*) With the hard work held equal, sub-elite runners who did
    about four fifths of their running easy improved more over 10 km than those who did two thirds at threshold (Esteve-Lanao and
    colleagues, 2007). The extra intensity a short race needs comes from intervals, not from harder easy days.
63. **Intervals of a few minutes near 5K pace are the main session.** [R] (*strong*) Intervals of 2 to 4 minutes, between
    threshold and maximal aerobic pace, improve race performance more than all-out sprints (Rosenblat and colleagues, 2020).
    For a 5K or 10K goal Periodize My Run alternates 5K-pace and 10K-pace intervals week by week, with threshold work alongside. [C]
64. **Short all-out efforts help only if volume holds.** [R] (*moderate*) Repeated 30-second sprints improved 10K time when
    weekly volume fell by a quarter, but not when it fell by two thirds (Bangsbo and colleagues, 2009; Iaia and colleagues, 2009).
    Periodize My Run keeps volume and uses relaxed 200 m repeats and strides for speed instead.

## 12. Ultras and hilly trail races

What is known here comes mostly from laboratory studies of hills, race records and surveys of finishers. There are almost no trials
of ultra training, so read these as the best available reasoning, not proven method.

65. **In long ultras the legs give out before the lungs.** [R] (*moderate*) Muscle damage, above all from running downhill,
    limits performance more than aerobic capacity, economy or the gut (Tiller and Millet, 2024). Uphill running works the hips
    harder; downhill running loads the thighs as they lengthen, which is what damages them (Vernillo and colleagues, 2017).
66. **Practise descending.** [R] (*strong* that it protects; *limited* on how often) One session of downhill running reduces the
    muscle damage from the next, for up to about nine weeks; eccentric and plyometric strength work gives a smaller version of the
    same protection (Bontemps and colleagues, 2020). For a hilly goal race, Periodize My Run adds 15 to 30 minutes of steady downhill
    running to the long run every third week of the specific phase. [P]
67. **Train on ground like the race.** [C] Weekly climb rises toward the race's climb per mile over the final months; an injury
    review also linked low yearly climbing and mostly-asphalt training with more injury in trail runners (*limited*).
68. **Walk the steep climbs.** [R] (*moderate*) On steep enough ground, walking costs less energy than running at the same rate of
    climb, and poles mainly make it feel easier (Giovanelli and colleagues, 2016, 2019). In races of three hours or more, the
    pacing plan marks every sustained climb of 20% or steeper for walking. The 20% line is this project's choice, set below the
    gradient where the laboratory found the crossover, because tired legs and slower climbers favour walking sooner. [P]
69. **Volume and experience matter most.** [R] (*moderate*) Previous ultra finishes, marathon best and weekly training volume
    predict ultra performance best (Knechtle and colleagues, 2010). Long runs stay easy, and in the specific phase a medium run
    the day before the long run practises running on tired legs. [C]
70. **Start slower than feels necessary.** [R] (*moderate*) Across 13,829 results from the Ultra-Trail du Mont-Blanc, a steadier
    pace went with a faster finish, in men and women and in every age group (Suter and colleagues, 2020). Pacing at the Western States
    100 has been analysed for 3,837 finishers by sex, age and performance level (Markovic and colleagues, 2025); the abstract was read
    and not the paper, so the common advice that the fastest runners start relatively slower is kept as coaching practice. [C]
71. **Eat from the start, and keep eating.** [R] (*strong*) At least 30 to 50 g of carbohydrate an hour, more if your gut is
    trained to it (Tiller and colleagues, 2019). Drink to thirst; drinking too much, not too little, causes the dangerous fall in
    blood sodium (Hew-Butler and colleagues, 2015).
72. **No ibuprofen during an ultra.** [R] (*strong*) In a randomised, placebo-controlled trial, ibuprofen during an ultra raised
    the rate of acute kidney injury from 34% to 52% (Lipman and colleagues, 2017).
73. **Plan for the night.** [R] (*limited*) In races through the night most runners nap, usually for under 30 minutes, and most bank
    extra sleep in the week before; four in five report symptoms of sleep loss, including falls and hallucinations (Martin and
    colleagues, 2018). Periodize My Run adds these points to the race-day notes when the predicted time is 18 hours or more.

## 13. Measurement limits

74. **Wrist heart rate is imperfect.** [R] (*moderate*) Wrist monitors agree less well with a medical ECG than chest straps do,
    and in one comparison a Garmin wrist monitor agreed least well of the devices tested (Gillinov and colleagues, 2017). They are
    least reliable at high intensity and in the cold, so Periodize My Run uses heart rate over minutes, never seconds, and a chest strap
    improves everything heart-rate based.
75. **A watch's fitness estimates are approximate.** [R] (*moderate*) Garmin's VO2max estimate was within about 7% of laboratory
    values on average (Carrier and colleagues, 2025), and is thrown off by heat, terrain and a wrong maximum heart rate.
76. **A watch's distance on a treadmill is a guess.** [P] Treadmill runs are judged by heart rate and time.
77. **A watch's altitude can be wrong.** [P] Each watch's altitude is checked on runs that start and finish in the same place,
    and hills are only adjusted for when it proves reliable.
78a. **A watch measures how long and when you slept well, but not the stages of sleep.** [R] (*moderate*) Against laboratory
    sleep recordings, six wearable devices including a Garmin were valid for the timing and duration of sleep, and all needed
    improvement for sleep stages (Miller and colleagues, 2022). Periodize My Run's decisions use sleep duration and timing only.
78. **Every score here is an estimate.** [P] Freshness, form, the execution score and the forecasts are this project's own
    measures built from watch data. They guide training; they do not diagnose anything.

## 14. Consistency, working life and sex

79. **Weeks strung together count for more than a fast build.** [R] (*moderate*) Among about 300,000 recreational marathon
    runners, a break of seven days or more in the build-up cost 5 to 8% in finishing time, measured against the same runner's
    marathons without one (Feely and colleagues, 2022). After a week or more without running, Periodize My Run holds the distance
    level for three weeks before building again, and the history page shows how many weeks you have gone without such a gap. [P]
80. **Hard running close to bedtime costs sleep; easy running does not.** [R] (*moderate*) In 14,689 people tracked for a year,
    strenuous exercise ending within four hours of falling asleep went with later sleep, shorter sleep, a higher overnight heart
    rate and lower heart-rate variability, and exercise ending four or more hours before sleep showed no effect (Leota and
    colleagues, 2025). Controlled trials agree that evening exercise does not harm sleep unless it is vigorous and ends within
    about an hour of bed (Stutz and colleagues, 2019; Frimpong and colleagues, 2021) (*strong*), and early-evening hard sessions
    did not disturb sleep in trained runners (Thomas and colleagues, 2020). Periodize My Run sets your own nights after late
    hard runs against your other nights and shows the difference, and says so on the morning after one, because that morning's
    heart-rate variability will read low for a reason other than fatigue. [P]
81. **Early training shortens sleep unless bedtime moves too.** [R] (*moderate*) Athletes slept much less before early-morning
    sessions than before rest days, because they woke earlier without going to bed earlier (Sargent and colleagues, 2014). This
    was measured in elite athletes; whether it holds for working runners is assumed, not shown. Periodize My Run counts your
    early runs that followed a short night.
82. **Life outside running changes what training does.** [R] (*moderate*) Athletes under more psychological stress are injured
    more often (Ivarsson and colleagues, 2017, a meta-analysis) (*strong*), people reporting high life stress recovered muscle
    function more slowly after hard exercise (Stults-Kolehmainen and colleagues, 2014) (*limited*), and those reporting the most
    stress gained least from the same aerobic training (Ruuska and colleagues, 2012) (*limited*). Periodize My Run does not ask
    about stress. It reads what stress does to sleep, resting heart rate and heart-rate variability, and it shows when the time of
    day you run has shifted. No study has tested what such a shift means, so it is shown as a pattern without a verdict. [P]
83. **Sex changes the advice, not the structure of the plan.** [R] (*moderate*) Women and men are injured at the same overall
    rate, but bone stress injuries are about twice as common in women and Achilles injuries more common in men (Hollander and
    colleagues, 2021, a meta-analysis) (*strong*). Men slow more than women in the second half of a marathon, 15.6% against
    11.7% on average (Deaner and colleagues, 2015). Across the menstrual cycle the average effect on performance is trivial and
    varies from person to person, so the evidence does not support planning training by cycle phase (McNulty and colleagues,
    2020) (*strong*). So Periodize My Run keeps the same plan structure for everyone, presses the patient start harder for men in
    long races, and adds what a bone stress injury feels like to a woman's warning about a jump in run length. [P]

## 15. Your own response, and an explanation for everything

84. **People respond differently to the same training, so the plan learns from your own record.** [R] (*moderate*) The spread in
    how people respond to identical training is real, though much of what looks like it is measurement noise (Hecksteden and
    colleagues, 2015), and people who do not improve on one dose do improve on a larger one (Montero and Lundby, 2017).
    Periodize My Run reads your whole history for two patterns, and lets each move the plan only a little and only when it is
    clear. Both are associations in one person's record, not experiments, and are shown with their sample size. [P]
85. **Your taper could be set from your own races, inside the range the research supports (off by default).** [R] (*strong*) Across trials the largest
    gains came from a two-week taper with volume cut by 41 to 60% and the fast running kept (Bosquet and colleagues, 2007). In
    158,000 recreational marathon runners, three weeks of steadily falling volume went with a 2.6% faster time than a minimal
    taper (Smyth and Lawlor, 2021) (*moderate*). For each of your past races of 15 km or more, Periodize My Run compares how
    deeply the last week was cut with how close the race was to your best level of the time. With six or more races and a clear
    pattern (a rank correlation of 0.4 or more), the taper is cut 5 points deeper or lighter; otherwise the research average
    stands. A deep taper may simply mark the races you cared about, so this is a hint, not proof. [P]
86. **Miles or hard running: which has raised your fitness (shown; off by default).** [P] Across the eight-week blocks in your history, the change in
    your watch's fitness estimate is compared with the miles and the number of hard runs in each block, after allowing for the
    level you started from. If miles clearly matter more, then before the race-specific phase every other week has one hard
    session, not two, with the same distance. If hard running matters more, both sessions stay. The watch's estimate is
    approximate (principle 75), which is why the pattern has to be strong before it counts. Principles 85 and 86 rest on few data points and a noisy watch estimate, so they are shown and change the plan only when the setting `apply_learned` is switched on.
87. **What decides a marathon time, and why runners stall.** [R] (*moderate*) Marathon pace is set by aerobic capacity, the
    fraction of it that can be held, and running economy (Joyner and Coyle, 2008), and by how well those hold up over hours
    (Jones, 2024). Faster runners hold a higher fraction of their critical speed: 93% for a 2:30 marathon against 79% for a 6:00
    one (Smyth and Muniz-Pumares, 2020). What separates faster runners in training is volume: weekly distance, runs per week,
    the number of runs of 20 miles or more, and the longest run all go with faster times (Doherty and colleagues, 2020), and the
    extra volume is almost all easy running, while a larger share of moderate and hard running goes with slower times
    (Muniz-Pumares and colleagues, 2024). These are comparisons between runners, not trials. They point to the usual reasons a
    runner stalls short of a time such as three hours: volume that has stopped rising, too much of it at a moderate effort, too
    little long running to hold pace late, and a first half run faster than can be sustained (Smyth, 2021). Periodize My Run
    shows which of speed and endurance your own gap is made of. [P]
88. **Every run has a stated purpose, and every decision an explanation.** [P] Each planned day says what it is for. "Explain my
    plan" lists each decision that shapes the plan, the numbers from your own data that led to it, and whether the rule behind
    it is research, coaching convention or this project's choice.

## 16. Weather

89. **Fitness is judged on what a run was worth in neutral weather.** [P] With weather switched on, each outdoor run is given
    the temperature, humidity, wind and rain it was run in. Its pace is then scaled by the same 0.35% per degree of WBGT, above
    15 °C or below 7.5 °C, before it counts as evidence of your threshold, your pace at a heart rate, or your time at threshold
    and race pace. A hot spell is therefore not read as lost fitness, nor a cool one as a gain. The size of the effect comes
    from race results (Mantzios and colleagues, 2022); applying it to training runs is this project's choice.
90. **Cold slows running too, but less is known.** [R] (*moderate*) The same race data show performance falling below the
    optimum range as well as above it (Mantzios and colleagues, 2022), and in the laboratory cold air did not by itself reduce
    endurance performance (Cheuvront and colleagues, 2005) (*limited*). Because the two disagree, Periodize My Run allows
    for cold when judging fitness only up to 1.5%, and does not ease the paces of a session for it. [P]
91. **Wind slows fast running; rain is recorded.** [R] (*moderate*) Running into wind costs energy that rises with the square of the wind
    speed, and running close behind another runner removes most of it (Pugh, 1970, 1971). In marathon results wind, humidity and rain had no
    effect of their own once temperature was allowed for (El Helou and colleagues, 2012; Vihma, 2010), because on a course that turns a headwind
    is partly given back and rain mostly comes with cooler air. Since version 2.10.1 the app eases fast paces for forecast wind on a loop route
    (about 2% at 20 km/h, 4.5% at 30, 7% at 40, up to 15%), a model anchored to Pugh's measurement with this project's own scaling, not a fitted
    figure. Rain changes nothing. A very windy day is still a reason to judge a session by effort, not pace. [P]
## 17. How runs felt, steady weeks, and getting used to heat

92. **A very hard effort on the watch counts as a recovery sign; a poor rating does not.** [R] (*moderate*) Self-reported measures of
    fatigue and effort track the response to training at least as well as the objective measures (Saw and colleagues, 2016). Garmin
    watches can ask for a feel and an effort rating after a run; nothing is ever typed into Periodize My Run. A last run (yesterday or
    today) rated 9 or 10 out of 10 for effort counts as one warning sign, and two such runs in the last four days count as two. They
    are added to the sleep, HRV and resting heart rate signs and ease the fast running the same way. A "weak" feel is stored and not
    counted: in the log of 74 competitive runners (section 18) a week with a very hard rated session went with 1.9 times the injury
    rate, and a week with a badly rated session with fewer injuries, not more. [P]
93. **Training monotony and strain are shown, not warned about.** [R] (*not supported here*) In 25 experienced athletes, illnesses
    clustered where a threshold of training strain (weekly load times monotony, the week's mean daily load divided by its standard
    deviation) was exceeded, with individual thresholds (Foster, 1998). In 42,766 days of the 74 competitive runners' log, a monotony
    of 2 or more on daily distance went with an injury rate of 1.06 times that of other days (95% interval 0.80 to 1.38), and the
    top tenth of strain with 0.80 times. Illness was Foster's outcome and injury is the log's, so this does not refute the study, but it
    gives no reason to warn on it. A review of 48 studies (19,390 athletes) does list increased training monotony and lack of tapering among
    the risk factors for acute respiratory illness (Derman and colleagues, 2022), so monotony is kept on the page. Periodize My Run shows monotony and strain on the Fitness page and no longer raises a watch-out. [P]
94. **Getting used to heat takes repeated hot runs over one to two weeks.** [R] (*strong*) Heat acclimatisation, the most important
    thing an athlete can do to reduce the strain of the heat, comprises repeated exercise-heat exposures over 1 to 2 weeks (Racinais and
    colleagues, 2015). With weather switched on, the Fitness page counts your runs of 30 minutes or more at a WBGT of 18 °C or more in
    the last 14 days, and the race-day forecast says how many you have had. The 18 °C line is this project's choice. The size of the
    benefit is not applied to the paces, because the consensus gives no figure to use. [P]
95. **Plans can be taken to other watches as a file.** [P] The coming days' sessions can be downloaded as FIT workout files (the format
    Garmin publishes), with the same pace and heart-rate targets as the Garmin calendar. Nothing is sent; whether a given watch accepts a
    FIT workout is up to that watch. Garmin watches read them from the NewFiles folder; COROS, Suunto and Polar have not been
    confirmed to import structured workouts from a file.

96. **The marathon-pace long run is the durability session.** [R] (*moderate*) How well pace and economy hold up after hours of running
    is an independent determinant of marathon performance, apart from aerobic capacity and threshold (Jones, 2024; Maunder and
    colleagues, 2021), and it falls less in faster runners (Smyth and colleagues, 2022). Both low and high intensity training improved it
    in sedentary and recreationally active adults on a bicycle (Matomäki and colleagues, 2023) (*limited* for runners), and strength training improved the durability of running economy late in 90 minutes of running
    (Zanini and colleagues, 2025) (*limited*). Periodize My Run's marathon-pace long run puts 3 easy miles first and the marathon-pace
    block after them, so that pace is practised on tired legs, and keeps the strength sessions through the specific phase (principle 33).
    How much durability work is enough has not been tested, so the amount is the same ladder as before. [P]
97. **Other training is shown, not counted.** [P] Cycling, swimming and other activities from the last four weeks are listed beside the
    running load. No study gives a fair exchange rate between a cycling hour and a running hour, so none is invented.
98. **A pattern that can go with not eating enough for the training is flagged, never diagnosed.** [R] (*moderate*) Low energy
    availability harms health and performance, and athletes often do not recognise it (Mountjoy and colleagues, 2023). A weight loss
    of 3% or more over eight weeks, with a recovery sign present and running of at least 15 miles a week, raises a note suggesting a
    conversation with a doctor or sports dietitian. The 3% and 15 miles are this project's choice, and a watch cannot screen for the
    condition itself. [P]

## 18. Checked against 6,582 real marathons

The rules above come from published research. This section is the project's own check of them against public data: the daily running
logs of 36,412 athletes in 2019, with the marathons they ran (Afonseca and colleagues, 2022; data CC BY 4.0), reproduced by
`tools/validate_public.py`. A race is a marathon-length day within a day of a 2019 Major, and only the autumn Majors (Berlin, Chicago, New
York) have 16 weeks of history in the 2019 file, so the sample is 6,582 autumn marathoners, mostly from Europe and the USA, who record
their running on a social network. Everything here is **association across runners, not cause**, and daily totals cannot tell one run from
two or a missed log from a missed day. [P]

99. **Weekly volume goes with faster marathons beyond what speed explains.** [P] (*moderate*, observational) Holding speed, sex and the
    other measures equal, each standard deviation more weekly distance in weeks 4 to 16 before the race went with a marathon about 5 to
    7% faster, the same in women and men and in all three age groups, and in both halves of the sample. Speed (the best training run of 5
    to 25 km) went with about 10% per standard deviation. This is the same direction as the meta-analysis (Doherty and colleagues,
    2020), and it supports building volume first (principles 19 and 87).
100. **The longest run added nothing once volume was known.** [P] (*limited*) The longest run in the build went with faster finishes on its
    own, but holding volume and speed equal its coefficient was close to zero (about 0.2%). Long runs and weekly volume are tangled
    together in this data: people who run long also run a lot. It does not show long runs are unimportant; it shows the data cannot
    separate them from volume, and the 3-hour cap (principle 30) is not contradicted.
101. **A very deep fall in the last three weeks went with slower finishes, a modest one with faster.** [P] (*limited*) Runners whose last
    three weeks averaged under 60% of their build had times about 2% slower than their speed predicted, and those at 80 to 100% about
    3% faster, against the average of weeks 4 to 16 (not the peak). That cannot be read as "taper less": a deep fall is also what an
    illness or an injury leaves, and these are different runners, not the same runner with two tapers. It does not argue against the
    taper principles (36 and 85), which rest on trials and on within-runner comparisons.
102. **A week or more without logged running was not clearly harmful here.** [P] (*not shown*) Its sign changed with what was adjusted
    for, so this data neither confirms nor refutes the 5 to 8% cost of a break found within runners (Feely and colleagues, 2022). A gap in
    a public log is often an unlogged run.
103. **Race equivalence works, with a known lean.** [P] (*moderate*) Turning each runner's best training run of 5 to 25 km into a marathon
    with the Daniels-Gilbert equations (the method behind the race predictions) gave a median error of 6.4% after one fixed adjustment,
    with 80% of runners within 12.8%. Training runs are slower than races, so the raw prediction is fast by about 7% on average: by
    3.7% for the fastest third of runners and 9.5% for the slowest third, which is what principle 87 says about slower runners holding
    a smaller fraction of their speed. Weekly volume and the longest run lowered the held-out error only from 6.7% to 6.3%. The app
    does not use training runs as race results: it learns its own lean from your races (principle 41).

104. **A build week is not planned more than 20% above the best of the last three.** [P] Running the planner on real athletes'
    histories (below) showed that, after a dip, a week could land 25 to 40% above recent weeks: two sessions and a long run have a
    minimum size, and so does a marathon-pace long run. Two changes follow. Under 20 miles of planned running a week, one session
    replaces two; and a marathon-pace long run is held back a week when it would lift the week past the line. This cut build weeks more
    than 20% above the best of the last three from 3.3% to 0.6%, at the cost of about 6% fewer marathon-pace long runs over a build
    (2.85 to 2.68 on average, with 6% of athletes getting none instead of 3%). The 20% line comes from the finding that raising a week by 20% to 60% was followed by more injuries (Damsted and colleagues,
    2019). [P]
105. **The planner was run on 1,500 real athletes' eight-week histories, 18 weeks each (`tools/validate_engine.py`).** [P] No crash and no
    hard days back to back. Planned peaks were about three quarters of what these runners actually ran (34 against 47 miles at the
    median), and the same for slow and fast runners because only eight weeks of history were given, where the app uses years. Runners who
    ran more than the plan's peak finished about 3.6% faster than their speed predicted, which fits principle 99 but is
    biased towards the runners who stayed healthy enough to race: the injured are not in the data, so it says nothing about whether
    running that much is safe.

106. **Whole history makes the plan safer and still conservative.** [P] Giving the planner every day the file held before the build (17 to
    25 weeks, where the earlier run used eight) cut build weeks more than 20% above the best of the last three from 0.6% to 0.3%, and
    raised the median planned peak from 34 to 38 miles against 55 actually run by this more committed group. The plan builds at about 6%
    a week, with a down week every fourth, so over 18 weeks it cannot reach what the fastest-building runners did. That rate is a design
    choice: weekly mileage change itself was not linked to injury (Frandsen and colleagues, 2025), only a long single
    run and jumps of 20% or more (Damsted and colleagues, 2019) were.
107. **A low-volume runner with a marathon goal is told how the plan shows the gap.** [P] Among runners starting under 15 miles a week, the
    planned long run was more than half the week in two thirds of build weeks, because the volume limit comes from recent running while the
    long run is sized for the distance. When that happens in three or more build weeks of a marathon or longer, the plan says so, and
    suggests a longer run-up, a shorter race first, or a finishing goal. The 50% is this project's choice; no study sets one.
108. **The plan is scored against what you did, and its predictions are kept.** [P] Each week's planned and run miles, and the share of key
    sessions and long runs completed (a run of 70% of the distance counts), are shown for the last 12 weeks. The race prediction for each
    coming A or B race is saved every week, so after the race the one made 8, 4 and 2 weeks before it is set against the result, not a
    prediction rebuilt afterwards. It cannot show that the plan caused a result.

109. **Seven days in a row without a rest day is noted.** [P] (*limited*) In the same log, a week with no rest day went with 1.34 times
    the injury rate of other weeks (95% interval 1.08 to 1.71, resampled by runner). It is one dataset of strong runners, so it is a
    note on the Plan page, not a rule; the plan itself always includes a rest day below seven running days.
110. **Of the rules tested on injury, a jump in the longest run and a very hard session held; a 20% jump in the week held weakly.** [P]
    In 42,798 weeks of the log (575 injuries, 74 runners), the injury rate was 1.33 times higher after a longest day more than 10% over
    the longest of the two weeks before (1.13 to 1.54; principle 22), 1.25 times after a week more than 20% above the best of the two
    before (1.01 to 1.55; principle 104), and 1.89 times after a session rated 0.9 or more for effort (1.32 to 2.67).
111. **How well the rules separate injured weeks is modest.** [P] Together, a longest-day jump, a 20% rise or a very hard session
    flagged 28% of weeks and caught 36% of injuries, with 1.45 times the injury rate in flagged weeks (1.23 to 1.69). Adding the
    no-rest-day note, 40% of weeks and 52% of injuries (1.61 times, 1.35 to 1.96). Counting a poor rating as a sign removed the signal altogether
    (1.04). The authors' own machine-learning models reached an AUC of about 0.68 on weekly data (Lövdal and colleagues, 2021): these
    rules are in that range, which is useful for a note and not enough to decide a day by.
112. **The test is `tools/validate_injuries.py`.** [P] Intervals come from resampling runners and move a little between runs. Data: Lövdal, den Hartigh and Azzopardi (2021), CC0, from DataverseNL. Runners are
    competitive and train with a team, so the numbers may not transfer to everyone, injury is whatever the team recorded, and the
    association between a rule and an injury is not proof that following the rule prevents one.

## Known gaps: where Periodize My Run does not yet follow the evidence

Listed so they are not mistaken for principles.

- **Feel is read only when the watch records it.** Self-reported fatigue, soreness and mood track the response to training at least as
  well as device measures (Saw and colleagues, 2016) (*strong*). Periodize My Run reads the feel and effort rating a Garmin watch can
  record after a run (principle 92), and nothing else: soreness and mood are not asked about. Whether Garmin returns the rating for
  your account has been tested only against stand-in data.
- **Weather** is used only if you switch it on, since it needs a weather service. Heat is estimated from temperature and
  humidity, not measured sun or wind, and takes no account of how used to heat you are, although two weeks of training in
  heat reduces its effect (Racinais and colleagues, 2015); the count of hot runs is shown (principle 94) but does not change a pace. Runs without a stored GPS track use your usual location, which is
  wrong for runs done elsewhere.
- **From age 50** only the down-week rhythm changes, not the spacing of hard days.
- **Time of day is reported, not planned.** Periodize My Run does not know when you will run a planned session, so it cannot warn
  before a late hard session, only after. Sleep onset comes from Garmin; with another watch source the sleep comparisons are not
  available.
- **A breakdown is inferred from gaps in your running**, unless you record being sick or injured. A long gap for another reason
  that is not a holiday you recorded will wrongly count against the block before it.
- **Ultra and trail training is still measured in distance.** Time on feet and climbing matter more than distance on the
  mountain, but the plan, the watch and the long-run limits still count miles. Hiking and pole practice, night running, heat
  and altitude preparation are not planned.
- **Ultra predictions** come from road fitness and ignore terrain, heat, night and altitude; for ultras the pacing plan shows how
  to spread effort, not times to hit.
- **Low energy availability** (not eating enough for the training) harms health and performance (Mountjoy and colleagues, 2023);
  Periodize My Run only flags a weight-loss pattern (principle 98); it cannot screen for the condition, which needs a conversation.
- **Altitude** is not planned: no adjustment for a high race or for training at height.

## References

Research named above. Only findings are used; no text, tables or figures are reproduced, and nothing here depends on material that may not be cited. The app lists the same sources, with the principles that use each, under How it works. Each was checked against its published record
(title, authors, journal and main finding) in October 2026 unless marked *from memory*; for those, check the paper before relying
on a detail.

- Bangsbo J and colleagues (2009). Reduced volume and increased training intensity elevate muscle Na+-K+ pump α2-subunit expression as well as short- and long-term work capacity in humans. *J Appl Physiol*. *Record confirmed.*
- Afonseca LA, Watanabe RN, Duarte M (2022). A worldwide comparison of long-distance running training in 2019 and 2020: associated effects of the COVID-19 pandemic. *PeerJ* 10:e13192. Data: figshare 10.6084/m9.figshare.16620238, CC BY 4.0. *Dataset description read; analysis is this project's own.*
- Lövdal SS, den Hartigh RJR, Azzopardi G (2021). Injury prediction in competitive runners with machine learning. *Int J Sports Physiol Perform* 16:1522–1531. Data: DataverseNL doi:10.34894/UWU9PV, CC0. *Dataset record and README read; analysis is this project's own; volume and pages from memory.*
- Banister EW (1991). Modeling elite athletic performance. In: *Physiological Testing of Elite Athletes*. Human Kinetics. *From memory; a book chapter.*
- Bassett DR, Howley ET (2000). Limiting factors for maximum oxygen uptake and determinants of endurance performance. *Med Sci Sports Exerc* 32:70–84.
- Bontemps B, Vercruyssen F, Gruet M, Louis J (2020). Downhill running: what are the effects and how can we adapt? A narrative review. *Sports Med*.
- Bosquet L, Montpetit J, Arvisais D, Mujika I (2007). Effects of tapering on performance: a meta-analysis. *Med Sci Sports Exerc*.
- Buist I and colleagues (2008). No effect of a graded training program on the number of running-related injuries in novice runners: a randomized controlled trial. *Am J Sports Med*.
- Carrier B, Marten Chaves S, Navalta JW (2025). Validation of aerobic capacity (VO2max) and pulse oximetry in wearable technology. *Sensors*.
- Casado A, Foster C, Bakken M, Tjelta LI (2023). Does lactate-guided threshold interval training within a high-volume low-intensity approach represent the "next step" in the evolution of distance running training? *Int J Environ Res Public Health*.
- Cheuvront SN, Carter R, Castellani JW, Sawka MN (2005). Hypohydration impairs endurance exercise performance in temperate but not cold air. *J Appl Physiol*. *Abstract read.*
- Costa RJS and colleagues (2017). Gut-training: the impact of two weeks repetitive gut-challenge during exercise. *Appl Physiol Nutr Metab*.
- Craven J and colleagues (2022). Effects of acute sleep loss on physical performance: a systematic and meta-analytical review. *Sports Med* 52:2669–2690.
- Damsted C, Parner ET, Sørensen H, Malisoux L, Hulme A, Nielsen RO (2019). The association between changes in weekly running distance and running-related injury: preparing for a half marathon. *J Orthop Sports Phys Ther* 49:230–238. *Abstract read.*
- Daniels J, Gilbert J (1979). *Oxygen Power: Performance Tables for Distance Runners*. A book; only its two published equations (the oxygen cost of running at a speed, and the fraction of capacity held for a given time) are used, not its tables. Not peer-reviewed.
- Deaner RO, Carter RE, Joyner MJ, Hunter SK (2015). Men are more likely than women to slow in the marathon. *Med Sci Sports Exerc*. *Abstract read.*
- Desai P, Jungmalm J, Börjesson M, Karlsson J, Grau S (2021). Recreational runners with a history of injury are twice as likely to sustain a running-related injury as runners with no history of injury: a 1-year prospective cohort study. *J Orthop Sports Phys Ther* 51:144–150. *Abstract read.*
- Derman W, Badenhorst M, Eken M, Gomez-Ezeiza J, Fitzpatrick J, Gleeson M, Kunorozva L, Mjosund K, Mountjoy M, Sewry N, Schwellnus M (2022). Risk factors associated with acute respiratory illnesses in athletes: a systematic review by a subgroup of the IOC consensus on "acute respiratory illness in the athlete". *Br J Sports Med* 56:639–650. *Abstract read.*
- Snyders C, Pyne DB, Sewry N, Hull JH, Kaulback K, Schwellnus M (2022). Acute respiratory illness and return to sport: a systematic review and meta-analysis by a subgroup of the IOC consensus on "acute respiratory illness in the athlete". *Br J Sports Med* 56:223–231. *Abstract read.*
- Hull JH, Loosemore M, Schwellnus M (2020). Respiratory health in athletes: facing the COVID-19 challenge. *Lancet Respir Med* 8:557–558. *Text read for the neck check.*
- Dial MB and colleagues (2025). Validation of nocturnal resting heart rate and heart rate variability in consumer wearables. *Physiol Rep*.
- Doherty C and colleagues (2020). An evaluation of the training determinants of marathon performance: a meta-analysis with meta-regression. *J Sci Med Sport* 23:182–188.
- Düking P and colleagues (2021). Monitoring and adapting endurance training on the basis of heart rate variability monitored by wearable technologies. *J Sci Med Sport*.
- Elliott N and colleagues (2020). Infographic. Graduated return to play guidance following COVID-19 infection. *Br J Sports Med*. *Record confirmed.*
- El Helou N and colleagues (2012). Impact of environmental parameters on marathon running performance. *PLoS One*. *Abstract read.*
- Ely MR, Cheuvront SN, Roberts WO, Montain SJ (2007). Impact of weather on marathon-running performance. *Med Sci Sports Exerc*.
- Esteve-Lanao J, Foster C, Seiler S, Lucia A (2007). Impact of training intensity distribution on performance in endurance athletes. *J Strength Cond Res* 21:943–949.
- Feely C, Smyth B, Caulfield B, Lawlor A (2022). Estimating the cost of training disruptions on marathon performance. *Front Sports Act Living*. *Abstract read.*
- Foster C (1998). Monitoring training in athletes with reference to overtraining syndrome. *Med Sci Sports Exerc* 30:1164–1168. *Abstract read.*
- Foster C and colleagues (2001). Differences in perceptions of training by coaches and athletes. *S Afr J Sports Med*. *From memory.*
- Fokkema T, van Damme AADN, Fornerod MWJ, de Vos RJ (2020). Training for a (half-)marathon: training volume and longest endurance run related to performance and running injuries. *Scand J Med Sci Sports*. *Abstract read.*
- Frimpong E, Mograss M, Zvionow T, Dang-Vu TT (2021). The effects of evening high-intensity exercise on sleep in healthy adults: a systematic review and meta-analysis. *Sleep Med Rev*. *Abstract read.*
- Granero-Gallegos A, González-Quílez A, Plews D, Carrasco-Poyatos M (2020). HRV-based training for improving VO2max in endurance athletes: a systematic review with meta-analysis. *Int J Environ Res Public Health* 17:7999. *Abstract read.*
- Gillinov S and colleagues (2017). Variable accuracy of wearable heart rate monitors during aerobic exercise. *Med Sci Sports Exerc* 49:1697–1703.
- Giovanelli N and colleagues (2019). Do poles save energy during steep uphill walking? *Eur J Appl Physiol*.
- Giovanelli N, Ortiz ALR, Henninger K, Kram R (2016). Energetics of vertical kilometer foot races; is steeper cheaper? *J Appl Physiol* 120:370–375.
- Grivas and colleagues (2026). Training variability and threshold density: a conceptual comparison of East African and Norwegian endurance training systems. *Front Physiol*.
- Haugen T, Sandbakk Ø, Seiler S, Tønnessen E (2022). The training characteristics of world-class distance runners. *Sports Med Open* 8:46.
- Hecksteden A and colleagues (2015). Individual response to exercise training: a statistical perspective. *J Appl Physiol*. *Abstract read.*
- Hellard P and colleagues (2006). Assessing the limitations of the Banister model in monitoring training. *J Sports Sci* 24:509–520.
- Hew-Butler T and colleagues (2015). Statement of the Third International Exercise-Associated Hyponatremia Consensus Development Conference. *Clin J Sport Med* 25:303–320.
- Hoogkamer W, Kipp S, Frank JH, Farina EM, Luo G, Kram R (2018). A comparison of the energetic cost of running in marathon racing shoes. *Sports Med* 48:1009–1019. *Abstract read.*
- Hollander K and colleagues (2021). Sex-specific differences in running injuries: a systematic review with meta-analysis and meta-regression. *Sports Med*. *Abstract read.*
- Hulme A, Nielsen RO, Timpka T, Verhagen E, Finch C (2017). Risk and protective factors for middle- and long-distance running-related injury. *Sports Med*. *Abstract read.*
- Hunter B, Muniz-Pumares D (2025). Durability of parameters associated with endurance running in marathoners. *Eur J Sport Sci* 25:e70073.
- Iaia FM and colleagues (2009). Four weeks of speed endurance training reduces energy expenditure during exercise and maintains muscle oxidative capacity despite a reduction in training volume. *J Appl Physiol*. *Record confirmed.*
- Impellizzeri FM, Tenan MS, Kempton T, Novak A, Coutts AJ (2020). Acute:chronic workload ratio: conceptual issues and fundamental pitfalls. *Int J Sports Physiol Perform* 15:907–913. *Record confirmed.*
- Ivarsson A and colleagues (2017). Psychosocial factors and sport injuries: meta-analyses for prediction and prevention. *Sports Med*. *Abstract read.*
- Jeukendrup A (2014). A step towards personalized sports nutrition: carbohydrate intake during exercise. *Sports Med*. *Record confirmed.*
- Jones A (2025). Road running age standards. Public domain (CC0).
- Jones AM (2024). The fourth dimension: physiological resilience as an independent determinant of endurance exercise performance. *J Physiol* 602:4113–4128.
- Joyner MJ, Coyle EF (2008). Endurance exercise performance: the physiology of champions. *J Physiol* 586:35–44.
- Knechtle B, Rosemann T, Knechtle P, Lepers R (2010). Predictor variables for a 100-km race time in male ultra-marathoners. *Percept Mot Skills* 111:681–693.
- Küster M and colleagues (2013). Consumption of analgesics before a marathon and the incidence of cardiovascular, gastrointestinal and renal problems. *BMJ Open*.
- Leota J and colleagues (2025). Dose-response relationship between evening exercise and sleep. *Nat Commun*. *Abstract read.*
- Lipman GS and colleagues (2017). Ibuprofen versus placebo effect on acute kidney injury in ultramarathons: a randomised controlled trial. *Emerg Med J* 34:637–642.
- Llanos-Lagos C, Ramirez-Campillo R, Moran J, Sáez de Villarreal E (2024). Effect of strength training programs in middle- and long-distance runners' economy at different running speeds: a systematic review with meta-analysis. *Sports Med* 54.
- Lopes TR and colleagues (2023). How much does sleep deprivation impair endurance performance? A systematic review and meta-analysis. *Eur J Sport Sci* 23:1279–1292.
- Lucia A, Hoyos J, Santalla A, Earnest C, Chicharro JL (2003). Tour de France versus Vuelta a España: which is harder? *Med Sci Sports Exerc* 35:872–878. *Record confirmed.*
- Manresa-Rocamora A and colleagues (2021). Heart rate variability-guided training for enhancing cardiac-vagal modulation, aerobic fitness, and endurance performance. *Int J Environ Res Public Health*.
- Mantzios K and colleagues (2022). Effects of weather parameters on endurance running performance: discipline-specific analysis of 1258 races. *Med Sci Sports Exerc*. *Abstract read.*
- Markovic S, Cuk I, Nikolaidis PT, Weiss K, Rosemann T, Scheer V, Thuany M, Knechtle B (2025). Pacing in ultra-marathon running: the Western States 100-mile endurance run 2006–2023. *Sci Rep* 15:8926. *Abstract read (part).*
- Martin T, Arnal PJ, Hoffman MD, Millet GY (2018). Sleep habits and strategies of ultramarathon runners. *PLoS One* 13:e0194705.
- Martínez-Navarro I and colleagues (2021). The week after running a marathon: effects of running vs elliptical training vs resting. *Eur J Sport Sci*.
- Matomäki P, Heinonen OJ, Nummela A, Laukkanen J, Auvinen EP, Pirkola L, Kyröläinen H (2023). Durability is improved by both low and high intensity endurance training. *Front Physiol* 14:1128111. *Abstract read. Sedentary and recreationally active adults, cycling: not runners.*
- Maunder E, Seiler S, Mildenhall MJ, Kilding AE, Plews DJ (2021). The importance of "durability" in the physiological profiling of endurance athletes. *Sports Med* 51:1619–1628. *Abstract read.*
- McNulty KL and colleagues (2020). The effects of menstrual cycle phase on exercise performance in eumenorrheic women: a systematic review and meta-analysis. *Sports Med*. *Abstract's conclusion read; authors and year from memory.*
- Meeusen R and colleagues (2013). Prevention, diagnosis, and treatment of the overtraining syndrome: joint consensus statement of the ECSS and the ACSM. *Med Sci Sports Exerc* 45:186–205.
- Midgley AW, McNaughton LR, Wilkinson M (2006). Is there an optimal training intensity for enhancing the maximal oxygen uptake of distance runners? *Sports Med* 36:117–132.
- Miller DJ, Sargent C, Roach GD (2022). A validation of six wearable devices for estimating sleep, heart rate and heart rate variability in healthy adults. *Sensors*. *Abstract read.*
- Minetti AE and colleagues (2002). Energy cost of walking and running at extreme uphill and downhill slopes. *J Appl Physiol*. *Record confirmed.*
- Mølmen KS, Øfsteng SJ, Rønnestad BR (2019). Block periodization of endurance training: a systematic review and meta-analysis. *Open Access J Sports Med*.
- Montero D, Lundby C (2017). Refuting the myth of non-response to exercise training: 'non-responders' do respond to higher dose of training. *J Physiol*. *Abstract read.*
- Mountjoy M and colleagues (2023). 2023 International Olympic Committee's (IOC) consensus statement on Relative Energy Deficiency in Sport (REDs). *Br J Sports Med* 57:1073–1097. *Record confirmed.*
- Mujika I, Padilla S (2000). Detraining: loss of training-induced physiological and performance adaptations. Parts I and II. *Sports Med* 30:79–87 and 145–154.
- Morton RH, Fitz-Clarke JR, Banister EW (1990). Modeling human performance in running. *J Appl Physiol* 69:1171–1177. *Abstract read.*
- Muniz-Pumares D and colleagues (2024). The training intensity distribution of marathon runners across performance levels. *Sports Med*.
- Nielsen RØ and colleagues (2014). Excessive progression in weekly running distance and risk of running-related injuries. *J Orthop Sports Phys Ther*.
- Paavolainen L and colleagues (1999). Explosive-strength training improves 5-km running time by improving running economy and muscle power. *J Appl Physiol* 86:1527–1533.
- Plews DJ and colleagues (2013). Training adaptation and heart rate variability in elite endurance athletes: opening the door to effective monitoring. *Sports Med*.
- Plews DJ, Laursen PB, Kilding AE, Buchheit M (2012). Heart rate variability in elite triathletes: is variation in variability the key to effective training? *Eur J Appl Physiol*.
- Pugh LGCE (1970). Oxygen intake in track and treadmill running with observations on the effect of air resistance. *J Physiol*. *Abstract read.*
- Pugh LGCE (1971). The influence of wind resistance in running and walking and the mechanical efficiency of work against horizontal or vertical forces. *J Physiol*. *Abstract read.*
- Raysmith BP, Drew MK (2016). Performance success or failure is influenced by weeks lost to injury and illness in elite Australian track and field athletes: a 5-year prospective study. *J Sci Med Sport* 19:778–783.
- Riegel PS (1981). Athletic records and human endurance. *Am Sci* 69:285–290.
- Racinais S and colleagues (2015). Consensus recommendations on training and competing in the heat. *Scand J Med Sci Sports* 25 Suppl 1:6–19. *Abstract read.*
- Rosenblat MA, Perrotta AS, Thomas SG (2020). Effect of high-intensity interval training versus sprint interval training on time-trial performance: a systematic review and meta-analysis. *Sports Med*.
- Ruuska PS and colleagues (2012). Self-rated mental stress and exercise training response in healthy subjects. *Front Physiol*. *Abstract read.*
- Casado A and colleagues (2022). Training periodization, methods, intensity distribution, and volume in highly trained and elite distance runners: a systematic review. *Int J Sports Physiol Perform*. *Abstract read.*
- Sandbakk Ø and colleagues (2025). Best-practice training characteristics within Olympic endurance sports as described by Norwegian world-class coaches. *Sports Med Open* 11:45.
- Saragiotto BT and colleagues (2014). What are the main risk factors for running-related injuries? *Sports Med*.
- Sargent C, Lastella M, Halson SL, Roach GD (2014). The impact of training schedules on the sleep and fatigue of elite athletes. *Chronobiol Int*. *Abstract read.*
- Saw AE, Main LC, Gastin PB (2016). Monitoring the athlete training response: subjective self-reported measures trump commonly used objective measures. *Br J Sports Med*.
- Frandsen and colleagues (2025). How much running is too much? Identifying high-risk running sessions in a 5200-person cohort study. *Br J Sports Med* 59:1203–1210.
- Seiler KS, Kjerland GØ (2006). Quantifying training intensity distribution in elite endurance athletes: is there evidence for an "optimal" distribution? *Scand J Med Sci Sports* 16:49–56.
- Seiler S and colleagues (2013). Adaptations to aerobic interval training: interactive effects of exercise intensity and total work duration. *Scand J Med Sci Sports*.
- Silva Oliveira P and colleagues (2024). Comparison of polarized versus other types of endurance training intensity distribution on athletes' endurance performance: a systematic review with meta-analysis. *Sports Med*.
- Smyth B (2021). How recreational marathon runners hit the wall. *PLoS One*.
- Smyth B and colleagues (2022). Decoupling of internal and external workload during a marathon: an analysis of durability in 82,303 recreational runners. *Sports Med*.
- Smyth B, Lawlor A (2021). Longer disciplined tapers improve marathon performance for recreational runners. *Front Sports Act Living*.
- Smyth B, Muniz-Pumares D (2020). Calculation of critical speed from raw training data in recreational marathon runners. *Med Sci Sports Exerc*. *Abstract read.*
- Southward K and colleagues (2018). The effect of acute caffeine ingestion on endurance performance: a systematic review and meta-analysis. *Sports Med*.
- Stöggl T, Sperlich B (2014). Polarized training has greater impact on key endurance variables than threshold, high intensity, or high volume training. *Front Physiol* 5:33.
- Stults-Kolehmainen MA, Bartholomew JB, Sinha R (2014). Chronic psychological stress impairs recovery of muscular function and somatic sensations over a 96-hour period. *J Strength Cond Res*. *Abstract read.*
- Stutz J, Eiholzer R, Spengler CM (2019). Effects of evening exercise on sleep in healthy participants: a systematic review and meta-analysis. *Sports Med*. *Abstract read.*
- Stull R (2011). Wet-bulb temperature from relative humidity and air temperature. *J Appl Meteorol Climatol* 50:2267–2269. *From memory; only its formula is used.*
- Swain P, Biggins J, Gordon D (2020). Marathon pacing ability: training characteristics and previous experience. *Eur J Sport Sci*. *Abstract read.*
- Suter D, Sousa CV, Hill L, Scheer V, Nikolaidis PT, Knechtle B (2020). Even pacing is associated with faster finishing times in ultramarathon distance trail running: the "Ultra-Trail du Mont Blanc" 2008–2019. *Int J Environ Res Public Health* 17:7074. *Abstract read.*
- Tanaka H, Seals DR (2008). Endurance exercise performance in Masters athletes: age-associated changes and underlying physiological mechanisms. *J Physiol* 586:55–63.
- Thomas C, Jones H, Whitworth-Turner C, Louis J (2020). High-intensity exercise in the evening does not disrupt sleep in endurance runners. *Eur J Appl Physiol*. *Abstract read.*
- Thomas DT, Erdman KA, Burke LM (2016). American College of Sports Medicine joint position statement: nutrition and athletic performance. *Med Sci Sports Exerc* 48:543–568.
- Tiller NB and colleagues (2019). International Society of Sports Nutrition position stand: nutritional considerations for single-stage ultra-marathon training and racing. *J Int Soc Sports Nutr* 16:50.
- Tiller NB, Millet GY (2024). Decoding ultramarathon: muscle damage as the main impediment to performance. *Sports Med* 55:535–543.
- Tønnessen E, Sandbakk Ø, Sandbakk SB, Seiler S, Haugen T (2024). Training session models in endurance sports: a Norwegian perspective on best practice recommendations. *Sports Med* 54:2935–2953.
- van der Worp MP and colleagues (2015). Injuries in runners: a systematic review on risk factors and sex differences. *PLoS One*.
- van Poppel D and colleagues (2021). Risk factors for overuse injuries in short- and long-distance running: a systematic review. *J Sport Health Sci*. *Abstract read.*
- Vernillo G and colleagues (2017). Biomechanics and physiology of uphill and downhill running. *Sports Med* 47:615–629.
- Vickers AJ, Vertosick EA (2016). An empirical study of race times in recreational endurance runners. *BMC Sports Sci Med Rehabil*.
- U.S. Food and Drug Administration (2008). Boxed warning on fluoroquinolone antibiotics: tendinitis and tendon rupture. Not peer-reviewed; a regulator's safety communication. *From memory.*
- Vihma T (2010). Effects of weather on the performance of marathon runners. *Int J Biometeorol*. *Abstract read.*
- Walsh NP and colleagues (2021). Sleep and the athlete: narrative review and 2021 expert consensus recommendations. *Br J Sports Med* 55:356–368.
- Wang Z and colleagues (2023). Effects of tapering on performance in endurance athletes: a systematic review and meta-analysis. *PLoS One*.
- Wingo JE, Ganio MS, Cureton KJ (2012). Cardiovascular drift during heat stress: implications for exercise prescription. *Exerc Sport Sci Rev*. *Record confirmed.*
- Zanini M, Folland JP and colleagues (2025). Strength training improves running economy durability and fatigued high-intensity performance in well-trained male runners: a randomized control trial. *Med Sci Sports Exerc*.
