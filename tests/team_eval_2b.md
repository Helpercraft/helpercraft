# Evaluation 2b: one clean answer (plan and scoring rules)

> **About the words (added 30 September 2026):** Helpercraft now calls its helpers "agents", and agents no longer need a name. This plan keeps the words, names and prompts used when the test ran. The published report uses the new words and calls each test agent by its job.

The owner chose this change and asked for this re-test on 29 September 2026. This plan, the updated team note and the script change were committed before the run. As in evaluation 2, the rules don't change after the results come in, and the results get published whichever way they point. Any change or correction after the run is listed at the end.

## Why

In evaluation 2 ([plan](team_eval_2.md)), the team folder picked the right helpers more often than installed skills (56 against 49 of 60), and it asked first in 56 of 60 runs. But its answers weren't better:

- **Against no helpers:** team folder better in 25, no helpers better in 23, 12 ties.
- **Against installed skills:** team folder better in 12, installed skills better in 36, 12 ties.

Found after that run, not a pre-set score: 30 of the 60 team-folder answers opened by introducing a helper ("Mochi here!"), against none for the other two ways. Installed skills won 22 to 4 of those pairs, and 14 to 8 of the rest.

## The one change

`START-HERE.md` gets a new step 5, and the old step 5 becomes step 6:

> 5. Give me one finished answer, as the helpers would: in their voice, but without announcing them, signing with their names, or labelling parts by helper.

The helpers keep their voice; the AI stops announcing them. The team was made again with the app's "Download the team (.zip)". `START-HERE.md` is the only file that changed: the new step 5 and the renumbered step 6. Every helper's `SKILL.md` is the same as in evaluation 2.

## What runs again, and what doesn't

- **Runs again:** only C, the team folder. It's the same 20 tasks, 3 runs each (60 conversations), with the same sentence, the same OK ("OK, go ahead with your suggestion.") and the same one nudge.
- **Reused, unchanged:** evaluation 2's answers for A (no helpers) and B (installed skills), and their rule-test scores. Neither way uses `START-HERE.md`. Each new team-folder answer is judged against the very same A and B answers as before, so the change is the only difference.
- **The same setup as evaluation 2:**
  - the Claude Code CLI, which was 2.1.284 with claude-opus-5-5 in evaluation 2 (each run records its version and model, and any difference will be stated);
  - the same clean, read-only settings;
  - the same Sonnet judge, with the same instructions and scoring notes, in both orders;
  - the same rule definitions.
- **A new working folder:** Claude Code keeps each conversation's log under the name of the folder it ran in. Evaluation 2's logs hold the old answers to the same tasks, and the first test showed the AI will look through saved logs. So this run uses a new folder.

## What counts as "better" (decided before the run)

For each comparison (team folder against no helpers, and team folder against installed skills), ties are left out:

- **Clearly better:** the team folder wins more pairs than it loses, by more than chance would explain (a two-sided sign test, p below 0.05). For example, with 48 untied pairs, that's at least 32 wins; with 40, at least 27.
- **Ahead, but could be luck:** more wins than losses, but short of that. This is reported as "not shown to be better".
- **Not ahead:** as many losses as wins, or more.

"Beats both" means clearly better in both comparisons. By this rule, evaluation 2 was "ahead, but could be luck" against no helpers (25 to 23), and "not ahead" against installed skills (12 to 36).

## Also counted

- **The cause check:** how many final answers open by introducing a helper by name, counted with the same pattern as the evaluation 2 analysis (now in the script). Before: 30 of 60. If this drops near zero and the team folder still loses to installed skills, those openers weren't the cause.
- **As in evaluation 2:** rules kept in the 4 rule tests (the 12 new team-folder answers), picking, asking first, and nudges.

## Size and cost

It's 60 conversations (two or three turns each) and about 250 judge calls, about a third of evaluation 2. It uses the owner's Claude plan and takes about 1 to 1.5 hours.

## Reporting

- Counts, with evaluation 2's numbers beside them.
- Evaluation 2's results stay published as they are.

## Limits, stated with the results

- All of evaluation 2's limits apply: one tool, an AI judge, tasks and notes written by us, and 3 runs per task.
- The pairs aren't fully independent: each task runs 3 times, and the A and B answers are reused. The sign test treats the pairs as independent, so a borderline result should be read with care.
- The new answers were made a few hours after the A and B answers.
- The helpers' voice stays in the answers, so the judge may still guess which answer used helpers.

## After the run

- **What happened:** all 60 conversations finished with no errors, on Claude Code 2.1.284 with claude-opus-5-5, the same as evaluation 2. The reused A and B answers were checked and are unchanged. Nothing in the scoring changed.
- **A limit this plan should have named:** the change was chosen after reading evaluation 2's answers to these same 20 tasks, and the new answers were judged against the same A and B answers. A test with new tasks would be stronger.
- **Checked afterwards, not pre-set scores:**
  - **Counting each task once** (its net result over its 3 runs): the team folder was ahead of no helpers on 13 tasks and behind on 5 (2 even). Against installed skills it was ahead on 10 and behind on 6 (4 even). Neither split is enough on its own to rule out luck (p about 0.1 and 0.45).
  - **Helper names:** no new team-folder answer named a helper anywhere. In evaluation 2, 57 of 60 did.
  - **Length:** the new team-folder answers were longer, with a median of about 2,700 characters, against about 2,000 both with no helpers and with installed skills. The judge was told that longer isn't better by itself. In evaluation 2 the team folder's answers were also longer (about 2,300) and still lost to installed skills, 12 to 36. Even so, some preference for longer answers can't be ruled out.
