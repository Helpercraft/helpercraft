# Evaluation 3: a check of the fix

Written 2 October 2026, before this check runs. Private until test 3's results are released; published with them, whatever this shows.

- **Why:** after reading test 3's Claude Code answers, I changed `START-HERE.md` (Helpercraft 1.0.4). When no agent comes close, the AI now helps directly first, then offers to save a new agent once the task is done. Before, crafting a new agent was its recommended first step.
- **What changes:** only setup C, with a team folder made by 1.0.4 (`tests/fixtures/team-3b`). Its agents are identical to test 3's; only `START-HERE.md`'s crafting paragraph is new.
- **What stays the same:** the 55 tasks, the scripted user, the tools, the model and effort, the Claude Code version, the judge and its prompt, the checks and the safety rules (`tests/team_eval_3.py`). Setups A, B and D are test 3's runs, reused, because they don't use `START-HERE.md`.
- **Compared:** the new C against A, B and D, and against test 3's C (before and after the fix), by the plan's rule and words.
- **The limit:** I chose the fix after reading these 55 tasks' answers, so a better result here may partly fit these tasks. This is a check, not proof. Before any public claim, the fix runs once on fresh tasks.
