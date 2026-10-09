# Evaluation 4: a check of the fix

Written 8 October 2026, before this check runs. Private until Evaluation 4's results are released; published with them, whatever this shows.

- **Why:** after reading Evaluation 4's answers, I changed three lines of `START-HERE.md`.
  - Step 5 asks the AI to save each thing I'll print, send or use as its own file. In Evaluation 4 the team folder saved files in 29 of 90 runs, against 69 for the plain AI.
  - Step 6 says that if an agent's rule would stop something I ask for, such as an offer I choose to make, the AI does what I ask unless it's unsafe.
  - The offer to save a new agent now comes only when no agent comes close.
- **What changes:** only setup C, with a team folder made by the fixed app (`tests/fixtures/team-4b`). Its 18 agents are identical to Evaluation 4's. Only those three lines of `START-HERE.md`, and its date, are new.
- **What stays the same:**
  - the 90 tasks, the pretend user, the tools, the model and effort, and the Claude Code version (2.1.285);
  - the judge and its prompt, the checks and the safety rules (`tests/team_eval_4.py`).
  - Setups A, B and D are Evaluation 4's runs, reused, because they don't use `START-HERE.md`.
- **Compared:**
  - the new C against A, B and D, and against Evaluation 4's C (before and after the fix), by the plan's rule and words;
  - the same lines as Evaluation 4: all 90 tasks, lengths within 20%, and without the 6 pilot tasks;
  - as behaviour: files saved, details used, checks passed and safety rules broken.
- **The limit:** I chose the fix after reading these 90 tasks' answers, so a better result here may partly fit these tasks. This is a check, not proof. Before any public claim of improvement, the fix runs once on fresh tasks.

## Decided before running (8 October 2026)

- **The date gap.** Evaluation 4's answers were written on 3 October; this check runs on 8 October.
  - The judge isn't told the date: I asked it, with its settings, and it answered "no date given".
  - The AI being tested is told the date, though. New answers plan from 8 October, and two tasks' dates (4 and 5 October) are now in the past.
- **Date-related tasks, by a fixed rule.** A task counts if its text, hidden details or checks name a date from 3 to 31 October, or say "this/next week", "this/next weekend", "this/next month", "tomorrow", "tonight" or "today". That gives 32 of the 90: t03, t05, t07, t11, t13, t15, t26, t28, t32, t36, t40, t41, t42, t48, t49, t50, t52, t54, t55, t56, t57, t60, t61, t62, t63, t64, t65, t74, t76, t77, t79 and t81.
- **So the main comparisons run on the same day (my decision).**
  - Today I also run A and the old team folder (`team-3b`) again, alongside the new team folder (`team-4b`). The main comparison (C vs A) and the before-and-after (C vs the old team folder) are then like for like.
  - B and D stay reused from 3 October.
  - Each verdict is also given without the 32 date-related tasks, as a secondary line beside "without the 6 pilot tasks".
- **Order.** First A and the old team folder (`run --team team-3b --setups AC`), then the new team folder (`run --team team-4b --setups C`), one after the other. Then one results file holds today's A, O (the old folder) and C, with Evaluation 4's B and D (`check-merge`). It's then checked, judged and scored.
- **Cost.** About $100 API-equivalent, on my plan's usage: 270 conversations and 720 judge verdicts.
