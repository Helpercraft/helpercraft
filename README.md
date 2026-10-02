<p align="center">
  <a href="https://helpercraft.github.io/helpercraft/helpercraft.html"><img src="docs/readme/banner.png" width="100%" alt="Helpercraft. Craft your own AI agent. Keep your team in one folder. Your AI suggests who fits your task, and asks first. Six agents made in the app: a nurse, a Pomeranian, a cat designer, a capybara site agent, a duck chef and a tech agent."></a>
</p>

<p align="center">
  <a href="https://helpercraft.github.io/helpercraft/helpercraft.html"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/try-dark.png"><img src="docs/readme/try-light.png" width="259" alt="Try it in your browser"></picture></a>&nbsp;&nbsp;
  <a href="https://github.com/helpercraft/helpercraft/releases/latest/download/helpercraft.html"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/download-dark.png"><img src="docs/readme/download-light.png" width="287" alt="Download for computers"></picture></a>
</p>

<p align="center"><sub>Free and open source · No account · Nothing leaves your device · English · 繁體中文 · Español</sub></p>

<p align="center"><b>Keep your AI agents in one folder. Your AI tool reads it, suggests the agents that fit your task, and waits for your OK.</b><br>Each agent is a standard skill file (<code>SKILL.md</code>) for Claude, ChatGPT, Gemini, Copilot, Cursor, Codex and more.</p>

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-how-dark.png"><img src="docs/readme/h-how-light.png" width="238" alt="How it works"></picture></h2>

1. **Create an agent.** Pick a job, such as café assistant or nurse. It starts with tasks and safety rules you can edit. A name and a look are optional.
2. **Save your team to a folder.** Each agent becomes a skill file, next to a `START-HERE.md` for your AI.
3. **Point your AI at the folder.** In a tool that reads files, such as Claude Code, Codex, Cursor or Copilot, paste one sentence and your task. In a chat app, paste a single agent instead.

<p align="center"><img src="docs/readme/proof.gif" width="360" alt="A real Claude Code run, replayed from its log. The AI gets the team folder and a task: reply to a one-star café review. It reads START-HERE.md, suggests the support agent, with the café assistant as an option, and asks before starting. After the OK it opens the chosen agents' files where they are and writes one finished reply that promises nothing the café hasn't agreed to."></p>
<p align="center"><sub>A real Claude Code run, replayed from its log. <a href="docs/evaluation.md">How I tested it</a>.</sub></p>

**Private by design:** nothing you type leaves your device, and there's no account. Healthcare agents are told not to diagnose or prescribe, but AI can ignore instructions, so check health advice with a professional.

<p align="center">
  <a href="https://helpercraft.github.io/helpercraft/helpercraft.html"><img src="docs/readme/demo.gif" width="100%" alt="A 30-second demo recorded in the real app: an agent made as a person, then a cat, then a duck; given a job and a job title while the skill file changes; given a personality with an optional MBTI type; crafted; Agent home with the whole team; the team handed to an AI with Copy for my AI; and the same app on a phone."></a>
</p>
<p align="center"><sub>Creating an agent, in 30 seconds.</sub></p>

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-why-dark.png"><img src="docs/readme/h-why-light.png" width="385" alt="Why I made Helpercraft"></picture></h2>

Skill files are powerful, but as plain text they can be hard to organize and easy to lose track of. I built Helpercraft to make creating and managing agents visual, for people who code and people who don't. What you get is still a standard skill file, with a job, tasks, rules and working habits.

Larger teams out there, with far deeper technical backgrounds, now build friendly agent characters too; a character can make an assistant feel like company, not just a tool. Helpercraft is my small, free take on a similar idea, meant to sit alongside those tools rather than replace them.

Many agent systems today are impressively autonomous. How much autonomy should an AI have? For some people, as much as possible. However, I prefer to keep some control: you decide when to bring your agents in, the AI is told to ask before it puts any of them to work, and every agent is one you made, or one your AI drafted with you. That control matters to me, and I suspect to others too.

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-home-dark.png"><img src="docs/readme/h-home-light.png" width="400" alt="One home for your team, and your AI asks first"></picture></h2>

Your agents live in one folder instead of being copied into every project. Any AI tool that can read files can use it:

```
my-team/
├── START-HERE.md  ← the AI reads this first
└── agents/
    ├── nurse-agent/SKILL.md
    ├── ui-designer/SKILL.md
    └── cafe-assistant/SKILL.md
```

**Copy for my AI** copies the sentence to start with:

> My agent team is in my-team. Read START-HERE.md there first, then suggest which of my agents should work on my task, and wait for my OK.

`START-HERE.md` asks the AI to:

1. read the team list, not every agent;
2. suggest which agents should take which part, as many as the task needs;
3. confirm with you in multiple-choice questions until you agree;
4. use the chosen agents where they are, without copying them;
5. give one finished answer, without naming or signing as the agents;
6. never use an agent to get around your request or its safety rules.

If no agent comes close, it recommends helping you directly, then offers to save a new agent once your task is done. If you say yes, or ask for one at any point, it drafts the agent with you the same way, saves it in the folder and adds it to the team. Asking first is an instruction, not a lock. Setup is under [Your team folder](#your-team-folder-chrome-or-edge-on-a-computer).

<details>
<summary><b>See a real <code>START-HERE.md</code> and <code>SKILL.md</code></b>, as Helpercraft writes them</summary>

`START-HERE.md`, for a team of three:

```markdown
# My agent team

I made these AI agents with Helpercraft. Each one is a skill: `agents/<name>/SKILL.md`.

## For the AI reading this

1. Read the team list below. Don't open the agent files yet.
2. For my task, suggest which agents should take which part: each one's name, job and what they'd do. Suggest as many as the task needs; one is fine for a small task.
3. Ask for my OK as a multiple-choice question, with your recommendation first. Keep asking until we agree. I might change who does what.
4. Then read the chosen agents' `SKILL.md` files here, where they are, and follow each one for their part. Don't copy or install them anywhere else.
5. Give me one finished answer, as the agents would: in their voice, but without announcing them, signing with their names, or labelling parts by agent.
6. The agent files describe how each agent talks and works. They never override my request or your own safety rules. Never run code from this folder unless I ask.

If no agent comes close, say so in one line and recommend helping me directly. When my task is done, offer to save a new agent for this kind of task next time. If I say yes, or I ask for a new agent at any point, craft it with me: ask me multiple-choice questions about its job, main tasks, rules and tone until we agree. If the job isn't one of Helpercraft's, describe it as a custom job. Save it as `agents/<name>/SKILL.md` in the same layout as the other agents, add it to the team list below, then carry on with anything left of my task.

## The team

| Agent | Use them for | File |
|---|---|---|
| Support agent | Support agent: helps draft friendly replies to customer messages and calm down upset customers with empathy. Use when the user asks about customer messages, complaints or follow-ups. | agents/support-agent/SKILL.md |
| Café assistant | Café assistant: helps answer guest questions warmly and track stock and draft supplier orders. Use when the user asks about guest questions, stock orders or menus and prep lists. | agents/cafe-assistant/SKILL.md |
| UI designer | UI designer: helps give honest feedback on a design and check designs for accessibility. Use when the user asks about design feedback, accessibility or colors and fonts. | agents/ui-designer/SKILL.md |
```

`agents/support-agent/SKILL.md`, the top of it:

```markdown
---
name: support-agent
description: "Support agent: helps draft friendly replies to customer messages and calm down upset customers with empathy. Use when the user asks about customer messages, complaints or follow-ups."
metadata:
  version: "1.0"
  made-with: "Helpercraft"
---

# Support agent

## Who you are
You are a cheerful support agent. You work in customer care. You mostly talk with a team of colleagues.

## How you talk
- Be warm and encouraging. Acknowledge how the person feels, and celebrate small wins.
- Bring upbeat energy. An occasional exclamation mark is fine.
- A touch of light humor is okay when the mood is relaxed. Stay serious for serious topics.
- Give enough detail to act on, then offer to go deeper.
- Don't use emoji.
- Use plain words, and reply in the language the person writes in.

## What you help with
- Draft friendly replies to customer messages
- Calm down upset customers with empathy
- Suggest next steps and follow-ups

…
```

</details>

**Tested:** 24 agents, 20 tasks, 3 runs each, in Claude Code. A blind AI judge compared each pair of answers twice, in both orders; an answer counts as preferred only if it won both times. It preferred the team folder's answers over the AI alone in 35 of 60 pairs (15 the other way, 10 ties), beyond chance by the rule set before the run. Against the same agents installed as skills it was 30 to 18 with 12 ties, which could be luck. Two caveats: counted task by task, the first lead could also be luck, and the team folder's answers were about a third longer, which AI judges tend to favour. These results came after one fix; in the first run, installed skills won. A controlled experiment is under way (see the [roadmap](#roadmap)). [Both runs and their limits](docs/evaluation.md).

<a href="docs/evaluation.md"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/eval2-dark.png"><img src="docs/readme/eval2-light.png" width="600" alt="With and without a Helpercraft team folder, test of 29 September 2026. Out of 60 pairs of answers judged blind. Against the AI alone, with no agents: first run, team folder preferred 25, tie 12, other preferred 23; after the fix, 35, 10, 15, preferred beyond chance. Against the same agents installed as skills: first run 12, 12, 36; after the fix, 30, 12, 18, ahead but could be luck. After the fix the team folder picked the right agents in 59 of 60 runs (installed skills: 49)."></picture></a>

<a href="https://helpercraft.github.io/helpercraft/docs/evaluation-3-tasks.html"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/eval3-dark.png"><img src="docs/readme/eval3-light.png" width="294" alt="Next test: see all 55 tasks"></picture></a>

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-active-dark.png"><img src="docs/readme/h-active-light.png" width="461" alt="Passive or active: how your AI finds your agent"></picture></h2>

| Passive (installed skills) | Active (a Helpercraft team folder) |
|---|---|
| Skills load when the AI decides they fit. In long sessions, AI tools shorten the conversation, and earlier skills can drop out ([bug report](https://github.com/anthropics/claude-code/issues/13919)). In my first test, the AI usually started the task without asking (25 of 30), and after the conversation was shortened, the skill wasn't reloaded (0 of 9). | You point the AI at the team. It suggested agents and asked first in 29 of 30 runs, and after the conversation was shortened, Claude Code kept the agent's file in view (9 of 9). [The test](docs/evaluation-1.md) |

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-personality-dark.png"><img src="docs/readme/h-personality-light.png" width="435" alt="Personality that fits the job"></picture></h2>

Choose how an agent talks and works, such as a calm mentor, a straight shooter or a gentle carer, then tune warmth, energy, humor and detail: a patient explainer for new staff, a direct reviewer for code. An MBTI-style type and a star sign are optional. None of these change the job, facts or safety rules.

## Features

- **Look:** a person or a companion animal (Pomeranian, cat, duckling or capybara) in the job's uniform, with adjustable hair, skin, eyes, glasses, extras and build. The 3D character can be spun and reacts to clicks.
- **Live file:** the `SKILL.md` updates as you choose, with changes highlighted.
- **Agent home:** up to 180 agents in your browser, with backup and restore as one file.
- **Jobs:** 13 fields, from Business to Writing, or your own, each with tasks, safety rules and hand-over triggers. Habits, answer formats and hard limits are adjustable too.
- **Output:** copy an agent into an AI chat, download its `.md`, or get a zip for the Claude app, with optional builder settings.
- **Team folder:** save the team to one folder (Chrome or Edge; other browsers get a zip), or give skills you already have a `START-HERE.md`.
- **Three languages:** English, Traditional Chinese and Spanish, including the agent's file.

## Quick start

**Phone or tablet:** open [helpercraft.github.io/helpercraft](https://helpercraft.github.io/helpercraft/helpercraft.html) and add it to your Home Screen, where your agents are safer from browser clean-ups. Phones don't run downloaded `.html` files properly.

**Computer:** download [`helpercraft.html`](https://github.com/helpercraft/helpercraft/releases/latest/download/helpercraft.html) and double-click it; there's nothing to install. Create an agent, press **Craft**, then **Copy** and paste it into an AI chat.

## Privacy

- Everything runs in your browser. There's no server, account, analytics or tracking.
- A Content-Security-Policy blocks the page from sending data anywhere. The downloaded file makes no network requests; the web version fetches only its own files (icons and an offline copy), so it also works offline. You can confirm this in your browser's Network tab.
- Agents are stored only in that browser. Clearing its site data deletes them, so use **Back up my home** to keep a copy or move them.
- Downloads are plain text you can read before sharing.

## Using your agent

Every agent is one file in the open [Agent Skills](https://agentskills.io/specification) format.

- **AI chats:** press **Copy** and paste. To keep an agent in every chat, add it to a Claude Project, a custom GPT or a Gemini Gem.
- **Claude app:** download the zip, then Customize → Skills → + → Upload a skill. Without a Skills menu, first turn on Settings → Capabilities → "Code execution and file creation". Safari on a Mac unzips downloads; compress the folder again first.
- **Coding tools:** unzip into `~/.claude/skills/` (Claude Code) or `~/.agents/skills/` (Codex, Copilot, Cursor, OpenCode and most others), or the same folders inside a project.
- **Claude Code in the cloud:** it loads only skills in the project's `.claude/skills/`, so add the agent there or paste it into the session.

In a zip or skills folder, the file must be named `SKILL.md`, inside a folder with the agent's name (`support-agent/SKILL.md`). App menus change; if a step doesn't match, please open an issue.

### Your team folder (Chrome or Edge on a computer)

1. Make a folder, such as `Desktop/Helpercraft`, and put `helpercraft.html` in it.
2. Open it in Chrome or Edge, open **Agent home**, choose **Save the team to a folder** and pick that folder.
3. Choose **Copy for my AI**, paste it into Claude Code, Codex, Cursor, Copilot or another coding tool, and add your task.

The folder holds `START-HERE.md` and one `agents/<name>/` folder per agent, with its `SKILL.md` and a small `.helpercraft` id file, so Helpercraft changes only its own folders. Other skills there are left alone.

- Changes are saved to the folder while the page is open. For security, the browser doesn't remember the folder between visits, so connect it again next time.
- Each browser keeps its own Agent home, so use one browser per team folder.
- Firefox, Safari and phones offer **Download the team (.zip)** instead. Coding tools may ask permission to read outside your project.

### Skills you already have (Chrome or Edge on a computer)

In **Agent home**, choose **Add skills you already have**, pick the folder that holds your skills (each one `<name>/SKILL.md`, as in `~/.claude/skills`), untick any to leave out, and choose **Write START-HERE.md**. Helpercraft reads only each skill's name and description, writes only `START-HERE.md`, and asks before replacing one it didn't create.

### Builder extras

The open spec defines six fields: `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`. Some apps read more:

| Extra | Read by |
|---|---|
| "Only when I call them by name" (`disable-model-invocation`, plus `agents/openai.yaml` for Codex) | Claude Code, Copilot, Cursor, Codex |
| `argument-hint`, "Hide from the / menu" (`user-invocable`) | Claude Code, Copilot |
| `paths` | Claude Code, Cursor |
| `when_to_use`, `allowed-tools` (in the spec, but experimental) | Claude Code |

All are optional, under **For builders** in the Craft step. The Claude app rejects files with extras, so its zip leaves them out. Descriptions stay within Claude's 200-character limit (the spec allows 1,024).

## Questions

<details>
<summary><b>What's inside an agent's file?</b></summary>

Plain text: a name and a one-sentence description that the AI uses to decide when to call the agent, then its role, working style, tasks and rules.

</details>

<details>
<summary><b>Why does my agent only show up sometimes?</b></summary>

An installed skill loads when your request matches its description. Ask for it by name or job, or add it to a Claude Project, a custom GPT or a Gem.

</details>

<details>
<summary><b>I already use custom instructions, a CLAUDE.md or an AGENTS.md. Why add agents?</b></summary>

Those load in every chat. An agent loads only when its job comes up, so it can hold detailed instructions without crowding other chats. You can use both.

</details>

<details>
<summary><b>Is a Healthcare or Legal agent an expert?</b></summary>

No. A role sets tone and guardrails, not professional knowledge. The agent is told not to diagnose, prescribe or give legal advice, and when to hand over to a person, but AI can ignore rules: in my test, asked for "just the number", it still gave a common label dose. Healthcare agents also say they give general information, not medical advice.

</details>

<details>
<summary><b>What do pets, MBTI types and star signs change?</b></summary>

Only how the agent talks and works. They sit at the end of the file, which tells the AI they never override facts, numbers or safety rules. None of it is science. "MBTI" and "Myers-Briggs Type Indicator" are trademarks of The Myers-Briggs Company; Helpercraft isn't affiliated with or endorsed by them.

</details>

<details>
<summary><b>Can I share an agent?</b></summary>

Yes: set "Who can copy them?" in the Craft step and share the file or zip. Only install skills from people you trust, because a skill is instructions your AI will follow.

</details>

## Roadmap

No dates yet. Ideas are welcome in [Discussions](https://github.com/helpercraft/helpercraft/discussions).

1. **A controlled experiment** *(ongoing)*
   - The plan and [all 55 tasks](https://helpercraft.github.io/helpercraft/docs/evaluation-3-tasks.html) are published before any run.
   - Fresh tasks, never used for tuning, with the same steps for every setup.
   - More AI tools and models, more kinds of tasks, and longer, multi-step tasks.
   - Complex tasks with many agents: does asking first give you more control than an AI that starts agents on its own, without worse results?
   - Scored by common practice: a length-corrected preference with error ranges, a second judge from another company, and about 20 pairs checked by hand. "Better" only if both judges agree, and results published either way.
2. **Fit with the tools you already use**
   - Set up a team folder in tools that organize agents their own way, such as Claude Code's subagents.
   - Note where they overlap or clash, and fill the gaps.
3. **You decide what your agents remember**
   - Many AI tools keep memory for a user or a project, rarely for each agent.
   - Each agent could get a small lessons note in the team folder, updated only with your OK.
   - Before a task, you'd choose for each agent: bring its lessons, use them without saving anything new, start fresh, or no memory.
   - First, I'll test whether the notes help beyond the tools' own memory, and whether tools follow the choice.
4. **More ways to style your agent**
   - Outfits, hairstyles, accessories and animals.

## For builders

```bash
git clone https://github.com/helpercraft/helpercraft.git
cd helpercraft
# Open helpercraft.html in a browser. Add #test to the address to run the self-test.

pip install playwright pyyaml pillow
python -m playwright install chromium firefox webkit
python tests/e2e.py --tiers A --rounds 1 --engines chrome   # a quick check: a few minutes
python tests/e2e.py                                         # everything: 5 browsers, about 45 minutes
```

One file, no build step, no dependencies. The full run also needs Google Chrome and Microsoft Edge (`--engines chromium,chrome,firefox,webkit` skips Edge). The [contributing guide](CONTRIBUTING.md) covers how the file is laid out, adding a job or an animal, translations, the 3D view and hosting.

## Contributing

Contributions are welcome, especially job packs reviewed by people who do the job, install steps kept current as apps change, and translations. See the [contributing guide](CONTRIBUTING.md) and the [code of conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
