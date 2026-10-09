# Tests 3 to 6: Helpercraft 1.0.3 to 1.0.5

Run from 2 to 8 October 2026 with Claude Code 2.1.285 and Claude Sonnet, in a clean setup with no personal settings, plugins or add-ons. Each plan and its scoring rules were committed before the test ran. The plans' names differ from the numbers here:
- [test 3](../tests/team_eval_3.md) ("Evaluation 3");
- [test 4](../tests/team_eval_3_check.md) (its check of a fix);
- [test 5](../tests/team_eval_4.md) ("Evaluation 4");
- [test 6](../tests/team_eval_4_check.md) (its check of a fix).

Every result is here, including the ones where Helpercraft lost. [Tests 1 and 2](evaluation.md) are reported separately.

<picture><source media="(prefers-color-scheme: dark)" srcset="readme/results-dark.png"><img src="readme/results-light.png" width="600" alt="How answers made with Helpercraft compared, every blind-judged test from 29 September to 8 October 2026. Against the AI alone: test 1, 25 preferred, 12 ties, 23 the other way, of 60; test 2, 35, 10, 15 of 60; test 3, 19, 12, 24 of 55; test 4, 25, 8, 22 of 55; test 5, 26, 15, 49 of 90; test 6, 43, 12, 35 of 90. Against the same agents installed as skills: test 1, 12, 12, 36; test 2, 30, 12, 18; test 3, 18, 9, 28; test 4, 26, 11, 18; test 5, 27, 22, 41; test 6, 37, 17, 36. Against the same agents as subagents the AI starts itself: test 3, 15, 10, 30; test 4, 17, 9, 29; test 5, 44, 18, 28; test 6, 59, 15, 16."></picture>

## In short

- In test 6, on 90 everyday tasks, Helpercraft 1.0.5 came out:
  - ahead of an AI that starts agents itself;
  - slightly but not clearly ahead of the same AI told to ask first;
  - even with the same agents installed as skills.
- Each fix helped on the tasks it was chosen on. 1.0.5 was preferred over 1.0.4 when both ran on the same day.
- Asking first seems to be most of what Helpercraft adds to the answers, and one sentence telling an AI to ask first does much the same.

## How the tests worked

- **Four ways, with the same 18 agents:**
  - **A:** the AI alone, told "Before you start, tell me your plan and ask for my OK as a multiple-choice question";
  - **B:** the agents installed as skills, with the same sentence;
  - **C:** a Helpercraft team folder;
  - **D:** the agents as subagents the AI starts itself, with no sentence.
- **Tests 3 and 4:** [55 everyday tasks](evaluation-3-tasks.html), 5 of them written by me. The person's only reply was "OK, go ahead with your recommendation". Test 4 ran the team folder again after a fix.
- **Tests 5 and 6:** 90 fresh tasks from 35 countries, written by a separate AI, with 1 to 6 or more steps each.
  - Each task came with details the person knew but hadn't typed. A pretend person gave those details when asked, as real people do.
  - Test 6 ran the team folder again after a fix. The AI alone and the old team folder ran again the same day.
- **The judge:**
  - Claude Sonnet saw each pair of answers twice, in both orders, without knowing which way made which. An answer counts as preferred only if it won both times.
  - "Preferred" means the low end of a 95% range from resampling the tasks is above 50%. With one judge, that's the strongest word this test can use.
- **A human check:** I rated 20 pairs from test 3 blind. My split (7 for the team folder, 10 against, 3 ties) was close to the judge's (6, 11, 3).

## Results

| Helpercraft against… | Test 3 (1.0.3) | Test 4 (1.0.4) | Test 5 (1.0.4) | Test 6 (1.0.5) |
|---|---|---|---|---|
| A: the AI alone, told to ask first | 46% (34–57%) | 53% (41–65%) | 37% (28–46%) | 54% (45–64%) |
| B: the agents as skills | 41% (29–53%) | 57% (46–69%) | 42% (33–51%) | 51% (41–60%) |
| D: subagents the AI starts itself | 36% (26–48%) | 39% (27–51%) | 59% (50–68%) | **74% (66–82%)** |

Each cell gives the preference for Helpercraft, with ties counted as half, and its 95% range. In test 6, 1.0.5 against 1.0.4 was **62% (53–71%)**.

- **Against D:** Helpercraft trailed in tests 3 and 4 (clearly in test 3), where asking first couldn't pay off because the person only said "go ahead". It came out ahead in tests 5 and 6, where the person answered questions.
- **Longer tasks:** I found no clear sign that Helpercraft helps more as tasks get longer.

## What each fix changed

- **1.0.4, after test 3.** In test 3, the team folder stopped to craft a new agent before helping on 8 tasks, and lost 20 of those 24 comparisons. Now, when no agent fits, the AI helps first and offers to save a new agent afterwards.
- **1.0.5, after test 5.** In test 5, the team folder saved its work as files far less often than the AI alone: 29 of 90 runs, against 69.
  - Now the AI saves each thing you'll print, send or use as its own file (87 of 90 runs in test 6).
  - It follows your own choices over an agent's rules unless that's unsafe.
  - It offers to save a new agent only when no agent fits.

## Limits

- One judge, from the same company as the AI being tested. There was one tool, Claude Code, and in these tests one model, Claude Sonnet. Other tools, models or settings may differ.
- I chose each fix after reading the same tasks' answers, so tests 4 and 6 are checks, not proof.
- The tasks and the pretend person are simulations. In test 6, B and D are test 5's answers, reused, because they don't use the team folder.
- With 55 or 90 tasks, a small difference reads as "no clear difference".
- The raw answers aren't published. The tasks, plans, scripts and team folders are in [tests](../tests).

## Run it yourself

With the Claude Code CLI signed in, `python tests/team_eval_4.py run --pilot` runs a small version of test 5. The script's header lists every step, including test 6's commands. It uses your plan.
