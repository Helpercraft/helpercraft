# Team-folder evaluation: plan and scoring rules

> **About the words (added 30 September 2026):** Helpercraft now calls its helpers "agents", and agents no longer need a name. This plan keeps the words, names and prompts used when the test ran. The published report uses the new words and calls each test agent by its job.

Written on 29 September 2026, before the full run. The rules below don't change after the results come in, and every result gets published, whichever way it points. Corrections made after the run are listed at the end.

## The question

Does an AI tool use a Helpercraft team the way the README says? And how does that compare with the same helpers installed as the tool's own skills?

## Setup

- **Tool:** the Claude Code CLI, with its default model. Each run records the version.
- **Clean setup:** `--setting-sources project --strict-mcp-config`, so no user hooks, plugins, MCP servers or personal settings load. Only Claude Code's own built-in skills and tools remain.
- **Tools in both modes:** Read, Glob, Grep and Skill. Nothing can be written or run.
- **Team:** `tests/fixtures/sample-team`, 8 helpers made with Helpercraft's "Download the team (.zip)":
  - Clover, nurse helper
  - Mochi, support agent
  - Luna, UI designer
  - Taro, maintenance tech
  - Pip, café assistant
  - Remy, coding buddy
  - Nova, tutor
  - Otto, lab technician
- **Active mode (the team folder):**
  - It starts from an empty project folder.
  - The team folder is added with `--add-dir`, as a user does when the tool asks.
  - The prompt is the "Copy for my AI" sentence plus the task.
- **Passive mode (installed skills):**
  - It starts from an empty project folder with the same 8 `SKILL.md` files in `.claude/skills/`.
  - The prompt is the task alone.

## Part 1: picking helpers

10 tasks × 3 runs × 2 modes. Each task names the helpers that **fit** and those that **must not** be picked; any other helper is an acceptable extra (see `TASKS` in `team_eval.py`). One task has no fitting helper.

- **Picked, active:** the helpers the reply proposes. A judge model extracts which helpers are suggested and which are rejected. It returns JSON and never sees which mode produced the reply.
- **Picked, passive:** the skills called with the Skill tool. This comes from the tool log.
- **Correct:** at least one helper that fits is picked, and no "must not" helper is. For the no-fit task, nothing is picked.
- **Recorded, but not scores:**
  - whether it asked before starting, meaning it asked to confirm or choose and hadn't already done the task. A question tacked onto finished work doesn't count;
  - whether the first reply already did the task;
  - whether START-HERE.md was read (active);
  - whether a helper's file was opened before the OK (active);
  - how many helpers were proposed for the multi-part task.

## Part 2: after the conversation is squeezed

3 tasks × 3 runs × 2 modes.

- **Passive:** the task, then `/compact`, then the probe.
- **Active:** the "Copy for my AI" sentence plus the task, then "OK, go with ⟨helper⟩", then `/compact`, then the probe.
- **The probe:** "Quick check before we go on: which helper are you working as right now? Name them and quote two of their rules."
- **Kept:** the reply names the expected helper, and at least one quoted rule matches that helper's file. A judge compares the rules against the file.
- **Calling the helper back:** one step in each mode. In active, you paste the "Copy for my AI" sentence again. In passive, you type the skill's slash command. Then the probe runs again.
- **Also recorded:**
  - whether the squeeze happened;
  - whether the probe was answered from memory or by re-reading the helper's file;
  - whether, after the OK, active read the chosen helper's file where it is.

## Changes after the pilot

A pilot of 2 tasks × 1 run in each mode (29 September) checked the scoring. It led to the two clarifications above: what counts as asking before starting, and recording re-reads after the squeeze. No tasks or pass rules changed.

## Counting

- Results are counts, like "27 of 30", not percentages.
- Timeouts and errors are counted separately, never as fails.

## Limits, stated with the results

- One tool only (Claude Code). Other tools come later.
- AI replies vary, so each case runs 3 times.
- The squeeze is a manual `/compact` after a short conversation, not a naturally long session.

## Fixed after the full run

Three sentences above were wrong. They were corrected on 29 September, after the full run. The original wording:

- The first line said: "Written on 30 September 2026, before the full run." The plan was committed on 29 September, before the full run started.
- Part 1 said: "Each task names the helpers that **must** be picked, those that are **acceptable** extras, and those that **must not** be picked" and "**Correct:** every "must" helper is picked and no "must not" helper is." The script committed with this plan, which is what ran, has always counted a pick as right when it includes at least one helper that fits. Under the stricter original wording, the team folder scores 28 of 30 and installed skills 24 of 30, instead of 29 and 27. The report shows both.

Two observations were added to the report after the full run. They're marked there as found in the logs, and they aren't scores: whether Claude Code put the helper's rules back in view right after the squeeze, and whether the AI dug through its saved copy of the old conversation before answering.
