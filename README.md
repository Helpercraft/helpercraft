<p align="center">
  <a href="https://helpercraft.github.io/helpercraft/helpercraft.html"><img src="docs/readme/banner.png" width="100%" alt="Helpercraft. Craft your own AI agent. Keep your team in one folder. Your AI picks who fits your task, and asks first. Six agents made in the app: a nurse, a Pomeranian, a cat designer, a capybara site agent, a duck chef and a tech agent."></a>
</p>

<p align="center">
  <a href="https://helpercraft.github.io/helpercraft/helpercraft.html"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/try-dark.png"><img src="docs/readme/try-light.png" width="259" alt="Try it in your browser"></picture></a>&nbsp;&nbsp;
  <a href="https://github.com/helpercraft/helpercraft/releases/latest/download/helpercraft.html"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/download-dark.png"><img src="docs/readme/download-light.png" width="244" alt="Download (one file)"></picture></a>
</p>

<p align="center"><sub>Free and open source · No account · Nothing leaves your device · English · 繁體中文 · Español</sub></p>

<p align="center"><b>Keep your AI agents in one folder. Your AI reads it, suggests which agent fits your task, and asks before it starts.</b><br>Each agent is a real skill file (<code>SKILL.md</code>) for Claude, ChatGPT, Gemini, Copilot, Cursor, Codex and more.</p>

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-how-dark.png"><img src="docs/readme/h-how-light.png" width="238" alt="How it works"></picture></h2>

1. **Make an agent.** Pick a job, like café assistant or nurse agent. It comes with tasks and safety rules you can change. Give it a name and a look too, if you like.
2. **Save your team to one folder.** Each agent becomes a skill file there, next to a `START-HERE.md` note for your AI.
3. **Point your AI at the folder.** In an AI tool that can read your files, like Claude Code, Codex, Cursor or Copilot, paste one sentence and your task. It suggests who fits and waits for your OK. In a chat app, paste one agent instead.

<p align="center"><img src="docs/readme/proof.gif" width="360" alt="A real Claude Code run, replayed from its log. The AI gets the team folder and a task: reply to a one-star café review. It reads START-HERE.md, suggests the support agent, with the café assistant as an option, and asks before starting. After the OK it opens the chosen agents' files where they are and writes one finished reply that promises nothing the café hasn't agreed to."></p>
<p align="center"><sub>A real Claude Code run, replayed from its log. <a href="docs/evaluation.md">See our tests</a>.</sub></p>

**Private by design:** nothing you type leaves your device, and there's no account. Healthcare agents are told not to diagnose or prescribe, but AI doesn't always listen, so check health advice with a professional.

<p align="center">
  <a href="https://helpercraft.github.io/helpercraft/helpercraft.html"><img src="docs/readme/demo.gif" width="100%" alt="A 30-second demo recorded in the real app: an agent made as a person, then a cat, then a duck; given a job and a job title while the skill file changes; given a personality with an optional MBTI type; crafted; Agent home with the whole team; the team handed to an AI with Copy for my AI; and the same app on a phone."></a>
</p>
<p align="center"><sub>Making an agent in the app, in 30 seconds.</sub></p>

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-why-dark.png"><img src="docs/readme/h-why-light.png" width="385" alt="Why I made Helpercraft"></picture></h2>

Skill files are powerful, but they're cold text files you write once and forget. I wanted an easier, friendlier place for new builders to make their AI agents and keep track of them, without writing code.

So in Helpercraft you craft your agent on screen, with a look, a job and a personality, and what you get is practical: a real skill file with a job, tasks, rules and good habits, ready for Claude, ChatGPT, Gemini, Copilot, Cursor, Codex and more. Your agents live together in Agent home, and in one folder your AI can read, so it can pick the right agent for what you're building.

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-home-dark.png"><img src="docs/readme/h-home-light.png" width="400" alt="One home for your team, and your AI asks first"></picture></h2>

Your agents don't get copied into every project. They live together in one folder, like a home, and any AI tool that can read files can visit it:

```
my-team/
├── START-HERE.md  ← AI reads first
└── agents/
    ├── nurse-agent/SKILL.md
    ├── ui-designer/SKILL.md
    └── cafe-assistant/SKILL.md
```

**Copy for my AI** gives your AI one sentence to start with:

> My agent team is in my-team. Read START-HERE.md there first, then suggest which of my agents should work on my task, and wait for my OK.

`START-HERE.md` then asks the AI to:

1. read the team list first, without opening every agent;
2. suggest which agents should take which part of your task;
3. wait for your OK, since you might change who does what;
4. use the chosen agents where they are, without copying or installing them anywhere else;
5. give you one finished answer in the agents' voice, without announcing them, signing with their names or labelling parts by agent;
6. treat each agent as how to talk and work, never as a way around your request or its own safety rules.

For example:

> **You:** Build my café's website. My agent team is in my-team…<br>
> **AI:** For this I'd suggest the **café assistant** for the menu and the **UI designer** for the look. OK?<br>
> **You:** Yes, go!

You stay in charge of who works on what. "Wait for my OK" is an instruction the AI follows, not a lock. How to set the folder up is under [Your team folder](#your-team-folder-chrome-or-edge-on-a-computer).

**We tested it:** 24 agents, 20 tasks, 3 runs each, with Claude Code and a blind AI judge. With the team folder, the judge preferred the answers over the AI alone in 35 of 60 pairs (15 the other way, 10 ties). Against the same agents installed as skills it was 30 to 18, with 12 ties: ahead, but that could still be luck. That's after one fix; in the run before it, installed skills won. [See both runs and the limits](docs/evaluation.md). More AI agents and models are planned.

<a href="docs/evaluation.md"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/eval2-dark.png"><img src="docs/readme/eval2-light.png" width="600" alt="With and without a Helpercraft team folder, test of 29 September 2026. Out of 60 pairs of answers judged blind. Against the AI alone, with no agents: first run, team folder better 25, tie 12, other better 23; after the fix, 35, 10, 15, clearly better. Against the same agents installed as skills: first run 12, 12, 36; after the fix, 30, 12, 18, ahead but could be luck. After the fix the team folder picked the right agents in 59 of 60 runs (installed skills: 49)."></picture></a>

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-active-dark.png"><img src="docs/readme/h-active-light.png" width="461" alt="Passive or active: how your AI finds your agent"></picture></h2>

| Passive | Active (what Helpercraft does) |
|---|---|
| Skills sit in a tool's skills folder and load when the AI thinks they fit. In long sessions, AI tools shorten the conversation, and skills loaded earlier can drop out ([bug report](https://github.com/anthropics/claude-code/issues/13919)). In our first Claude Code test, the AI usually started the job right away, without asking (25 of 30). After the conversation was shortened, the skill wasn't put back (0 of 9), and the AI dug through the old conversation to find it (8 of 9). | You point the AI at your team, by name or with **Copy for my AI**. It suggests who fits and asks first (29 of 30), so you stay in charge. After the conversation was shortened, Claude Code put the agent's file back in view (9 of 9). [See the test](docs/evaluation-1.md) |

<h2><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/h-personality-dark.png"><img src="docs/readme/h-personality-light.png" width="435" alt="Personality that fits the job"></picture></h2>

Pick how your agent talks and works: sunny, a calm mentor, a straight shooter, a curious mind, a gentle carer or a cheeky sidekick, then fine-tune warmth, energy, humor and detail. That's practical: a patient explainer for new staff, a straight shooter for code reviews, a gentle carer for patients' questions. The job, its tasks and its safety rules stay the same whatever the personality.

**Optional:** add an MBTI-style type and a star sign. Like the personality, they shape how your agent talks and works, and they never change the job, facts or safety rules. [More about them](#about-pets-mbti-types-and-star-signs).

## What you can do

- **Name & look:** start as a person or a pet companion (a fluffy Pomeranian, a cat, a duckling or a capybara); every kind wears the job's uniform. For people there are 14 hairstyles, 8 skin tones (two of them fantasy colours) and 10 hair colours. Animals get fur and marking colours instead. On top of that you can pick eye colour, eyebrows, four glasses styles, extras (freckles, lashes, a bow, a flower clip, earrings, a fruit hat) and a slim, regular or round build. All the characters are original designs. The 3D agent reacts as you go: you can drag to spin them, and they follow your cursor and wave when you click. Dogs and cats wag their tails.
- **Live file:** on wide screens, the file sits beside the character. Closed, it shows the agent's folder and pulses "3 lines changed" when a choice changes the file. Open, it shows the whole SKILL.md updating as you click, with changed lines highlighted. Smaller screens get a SKILL.md button instead.
- **Agent home:** every agent you craft moves in. There are 20 rooms with 9 spots each, and each spot shows the agent's portrait in their outfit with their name underneath. You can flip rooms with the arrows or by swiping, open any agent back in the studio, copy or download them, or release them. "Back up my home" saves everything to one file, and "Restore" brings it back. On a phone, backing up opens the share sheet, so you can email or AirDrop your agents to your computer and restore them there.
- **Job:** 13 fields, A to Z (Business, Customer care, Design, Education, Food & hospitality, Healthcare, Laboratory, Legal, Planning, Software & IT, Trades, Writing, or your own). Each comes with ready-made tasks, safety rules and "hand over to a person when…" triggers, and each job title starts with its own tasks ticked. Nothing is picked until you choose.
- **Personality:** six starting types, emoji and a catchphrase. **Fine details** (optional, nothing picked until you choose) add an MBTI-style type and a star sign.
- **Habits and rules:** how they work, what their answers look like (flowcharts for workflows, for example), and what they must never do.
- **Craft:** one file that works everywhere, with no app to pick. **Copy** your agent and paste them into any AI chat (Claude, ChatGPT, Gemini, Copilot…), on a phone or a computer. You can also download the `.md` file, named after your agent (like `Nurse-agent_Skill.md`), or a zip to keep them in the Claude app. Coding tools and builder extras are one tap further down.
- **Team folder:** on a computer, keep your whole team in one folder that any AI tool can read. The AI suggests which agents fit your task and waits for your OK.
- **Skills you already have:** point Helpercraft at a folder of skills made anywhere, and it writes the same `START-HERE.md` for them. Your skills aren't changed.
- **Three languages:** English, Traditional Chinese and Spanish. The little C · E · S switch under "Private" changes everything at once, including your agent's file, so the AI gets its instructions in your language. Helpercraft starts in your browser's language and remembers your choice. The skill's folder name stays in English letters in every language, so switching never renames it.

## Quick start

**On a phone or tablet:** open [helpercraft.github.io/helpercraft](https://helpercraft.github.io/helpercraft/helpercraft.html), and add it to your Home Screen to keep your agents safe. Phones don't run a downloaded `.html` file properly. iPhones, for example, show it in a preview. The hosted page is the same single file: once it has loaded, it still can't send anything anywhere.

**On a computer:**

1. Download [`helpercraft.html`](https://github.com/helpercraft/helpercraft/releases/latest/download/helpercraft.html).
2. Double-click it. It opens in your browser, with nothing to install.
3. Create your agent and press **Craft**.
4. Press **Copy** and paste your agent into any AI chat.

## Privacy

- It runs entirely in your browser, and the download is one file. There's no backend server, account, analytics or tracking.
- A Content-Security-Policy stops the page from sending anything anywhere. The downloaded file makes no network requests at all. The web version fetches only Helpercraft's own files from its own address (its icons and an offline copy of itself), so it can live on your Home Screen and open without internet. You can check for yourself: open your browser's developer tools and watch the Network tab while you use it.
- Your agents are saved only in that browser (localStorage), in Agent home. Clearing the browser's site data erases them, so use "Back up my home" to keep a copy, or to move your agents to another computer.
- What you download is plain text. You can read it before sharing it with any AI app.

## Using your agent

Every agent is one file in the open [Agent Skills](https://agentskills.io/specification) format. It works everywhere, so there's no app to pick.

- **Any AI chat, on a phone or a computer:** press **Copy** and paste. That's it. To keep them in every chat, paste them into a Claude Project, a custom GPT or a Gemini Gem. On a phone, **Share** sends your agent to email, messages or notes, so you can open them on your computer too.
- **Claude Code in the cloud (from a phone or the web):** cloud sessions don't load agents saved on your computer. They do load ones stored in the project at `.claude/skills/<name>/SKILL.md`. The simplest way is to paste your agent into the session.
- **Claude app:** download the zip, then Customize → Skills → + → Upload a skill. No Skills menu? Turn on Settings → Capabilities → "Code execution and file creation" first. Safari on a Mac unzips downloads: if you get a folder, right-click it and choose Compress.
- **Coding tools:** unzip into `~/.claude/skills/` for Claude Code, or `~/.agents/skills/` for Codex, Copilot, Cursor, Gemini CLI, Windsurf, OpenCode and most others. Inside a project, `.claude/skills/` or `.agents/skills/` keeps them to that project.

Inside a zip or a skills folder, the file must be called `SKILL.md`, in a folder with the agent's name (like `support-agent/SKILL.md`). That's how AI apps recognise it. The single `.md` download has a friendlier name, for reading or pasting.

App menus change. If a step doesn't match what you see, search your app's help for "skills", and please open an issue so we can update it.

### Your team folder (Chrome or Edge on a computer)

Keep your whole team as files that any AI tool can read, and let the AI pick the right agents for each task.

1. Make a folder, like `Desktop/Helpercraft`, and put `helpercraft.html` in it.
2. Open `helpercraft.html` in Chrome or Edge, open **Agent home** and choose **Save the team to a folder**. Pick that same folder.
3. Choose **Copy for my AI** and paste it into Claude Code, Codex, Cursor, Copilot, Gemini CLI or another coding tool, then add your task. The AI reads `START-HERE.md`, suggests which agents should do what, and waits for your OK.

The folder then holds:

```
START-HERE.md               the note for AI tools: the team list, and how to pick agents
agents/<name>/SKILL.md      one folder per agent
agents/<name>/.helpercraft  the agent's id, so Helpercraft knows which folders are its own
```

Good to know:

- While the page is open, crafting, updating, releasing and restoring keep the folder up to date. Helpercraft doesn't remember the folder between visits (any other page opened from a file could otherwise reach it), so connect it again next time.
- Helpercraft only changes folders it made. Other skills in `agents/` are left alone. An agent released while the folder wasn't connected stays there until you delete it; `START-HERE.md` only lists the current team.
- Each browser keeps its own Agent home, so use one browser per team folder, or move agents across with "Back up my home" and "Restore".
- Firefox, Safari and phones can't save into a folder. Agent home offers "Download the team (.zip)" with the same layout instead.
- Coding tools may ask before reading outside your project: Claude Code asks for permission, and Gemini CLI needs `/directory add` with the folder.
- "Wait for my OK" is an instruction the AI follows, not a lock.

### Skills you already have (Chrome or Edge on a computer)

Already have skills, made by hand or with another tool? Give them the same "suggest and ask first" note.

1. Open **Agent home** and choose **Add skills you already have**.
2. Pick the folder that holds your skill folders, where each skill is `<name>/SKILL.md`. For example, `~/.claude/skills` or a project's `.claude/skills`.
3. Untick any you want to leave out, then choose **Write START-HERE.md**.

Helpercraft reads only each skill's name and description. It writes one file, `START-HERE.md`, and copies the sentence for your AI. It never changes, moves or copies your skills, and it asks before replacing a `START-HERE.md` it didn't make.

### Builder extras

The open spec defines six fields: `name`, `description`, `license`, `compatibility`, `metadata` and `allowed-tools`. Some apps read more:

| Extra | Read by |
|---|---|
| "Only when I call them by name" (`disable-model-invocation`, plus `agents/openai.yaml` for Codex) | Claude Code, Copilot, Cursor, Codex |
| `argument-hint`, "Hide from the / menu" (`user-invocable`) | Claude Code, Copilot |
| `paths` | Claude Code, Cursor |
| `when_to_use`, `allowed-tools` (in the spec, but experimental) | Claude Code |

They're all optional, under **For builders** in the Craft step. Apps that don't know a setting ignore it, but the Claude app's upload rejects the whole file, so Helpercraft leaves extras out of the Claude app zip.

Descriptions have two different limits: Claude's help center says 200 characters, and the open spec allows 1,024. Helpercraft keeps every file at 200 or under, and spends that space on the topics that decide when your agent gets called.

## About pets, MBTI types and star signs

Like the other personality flavour, an agent's kind (person or pet) never changes facts or safety rules, and the one-sentence description apps use to decide when to call your agent stays the same.

They shape your agent's personality: how it talks and how it works, which also makes it nicer for social and study use. They go in a short section near the end of the file, after the job, its tasks and its rules, so they never change the job itself. They don't make it smarter, and the generated file tells the AI that they never override facts, numbers or safety rules. None of this is science.

"MBTI" and "Myers-Briggs Type Indicator" are trademarks of The Myers-Briggs Company. Helpercraft isn't affiliated with or endorsed by them. It uses the common four-letter codes with its own descriptions.

## Questions

**What's inside an agent's file?**
Plain text you can read. At the top: the agent's name and one sentence that tells an AI when to call them. Below: who they are, how they talk and work, and the rules they keep. An AI reads that top sentence first and opens the rest only when the job comes up.

**Why does my agent only show up sometimes?**
An installed skill wakes up when your request matches its description. Ask for your agent by its name or job, or paste them into a Claude Project, a custom GPT or a Gem to keep them in every chat.

**I already have custom instructions, a CLAUDE.md or an AGENTS.md. Why add an agent?**
Those are read at the start of every chat, needed or not. An agent waits until their job comes up, so they can carry long, detailed instructions without crowding your other chats. Many people keep both: an agent for the job, and always-on text for the personality.

**Is a Healthcare or Legal agent an expert?**
No. A role gives tone, good habits and guardrails. It doesn't give professional knowledge or a license. The built-in rules tell the agent not to diagnose, prescribe or give legal advice, and when to hand over to a person, but AI doesn't always follow its rules: in our test, asked for "just the number", it still gave a common label dose. Check health and legal advice with a professional. Healthcare agents go further: Helpercraft shows a reminder while you make one and once it's crafted, and the agent itself tells people, once per conversation, that it gives general information and suggestions, not medical advice.

**Can I share my agent?**
Yes. Choose "Who can copy them?" in the Craft step, then share the file or the zip. Only install skills from people you trust, because a skill is instructions your AI will follow.

## Roadmap

What we'd like to do next. There are no dates yet, and ideas are welcome in [Discussions](https://github.com/helpercraft/helpercraft/discussions).

1. **Bigger tests**
   - More AI tools and models.
   - More kinds of tasks.
   - Longer, multi-step tasks, where a team folder should matter most.

   Each test runs the same tasks with and without Helpercraft, judged blind, and we publish the results either way.

2. **Fit with the tools you already use**
   - Some AI tools already organize agents their own way, like Claude Code's subagents.
   - We'll set up a team folder in each one, step by step, note where they overlap or clash, and fill the gaps.

3. **You decide what your agents remember**
   - Many AI tools now keep their own memory, but for you or a project, not for each agent.
   - So instead of a second memory system, each agent would get a small lessons note in the team folder. It goes wherever the agent goes, and nothing is added without your OK.
   - Before a task, you pick which agents join and, for each one: bring its lessons, use them but save nothing new, start fresh, or no memory.
   - First we'll test whether the notes help beyond the tools' own memory, and whether the tools follow your choice.

4. **More ways to style your agent**
   - More outfits, hairstyles, accessories and pets.

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

The full run also needs Google Chrome and Microsoft Edge installed; `--engines chromium,chrome,firefox,webkit` leaves Edge out. The [contributing guide](CONTRIBUTING.md) has the rest of the checks.

- **What goes into an agent file:** at the top, the name and one description sentence (200 characters or fewer) saying what the agent does and when to call them, because that's what an AI reads to decide. Below come who they are, how they talk and work, their tasks, rules and hand-over points. The personality, pet kind, MBTI type and star sign sit in a short section at the end and never override the rules.
- **No build step.** It's one file with no dependencies. Open it in a browser and edit it in any text editor.
- **Self-test:** add `#test` to the address to run the built-in checks. They cover names, YAML quoting, every job and job title, the portable file and the Claude app zip, builder extras, zip structure, saved and restored agents, the team folder, and a byte-for-byte guard on the default file. Opened from a file, it skips the 5 folder checks, because those need the browser's private test folder, which pages opened from a file don't get.
- **End-to-end tests:** `python tests/e2e.py` clicks through Helpercraft the way a person would in Chrome, Edge, Chromium, Firefox and WebKit, at phone, tablet and computer sizes, in all three languages, opened as a file and from a local server. It also runs stress, broken-input and security tests. Setup is in the commands above, and everything stays on your computer.
- **Translations:** English text is the key. The Chinese and Spanish versions live in the page's `<script id="i18n">` block, and code asks for text with `T('English text', { name })`. The self-test fails if any text is missing a translation or its `{placeholders}`. To add or edit translations: `python tests/i18n.py pull` writes them to `tests/out/i18n/zh.json` and `es.json`; edit those, then `python tests/i18n.py check` and `python tests/i18n.py merge` to put them back into the page. `keys` lists every text and where it's used, and `sample zh` prints a whole agent in one language. To add a text, write it in English through `T()`, then add its Chinese and Spanish.
- **How the file is laid out:** `App` holds plain data tables (`ROLES`, `SPECIES`, `HAIRSTYLES`, `ARCHETYPES`, `MBTI_AXES`, `ZODIAC`, `HABITS`, `LICENSE_LIST`), the file generator (`buildSkill`), a small zip writer, Agent home storage (one key per agent plus a small index), and the interface. `Stage` is the 3D view (see below).
- **Add a job:** add one entry to `ROLES`. Give every task a topic in the same position in `topics`, and each job title 2–3 pre-ticked tasks in `picks`; the self-test checks both. Reuse a costume through `look.acc` (0–10) and `look.pattern` (0–7), so no 3D work is needed.

### Inside the 3D view

- **`Stage` is the showroom.** A single WebGL2 fragment shader draws every kind of agent from simple shapes (ray marching), with no libraries. The whole scene is sampled from one loop, so the GPU driver compiles it only once. That compile runs in the background, and the view adjusts its resolution to stay smooth. `Stage.portrait()` renders the Agent home thumbnails.
- **No 3D:** add `?nogl` to the address to turn off the 3D view. The character disappears and a short message shows instead.
- **Still picture:** on a computer too slow for the 3D (under about 10 frames a second even at the lowest sharpness, for 5 seconds), the character stands still and is redrawn only when something changes. A one-time note says so, and the browser remembers it for 7 days. Add `?still` to force it, or `?still=off` to never switch (the tests do that).
- **Add a pet kind or a hairstyle:** this is 3D work. A pet kind is a branch in the shader's `mapHead`, plus an entry in `SPECIES`. A hairstyle is a new part in `mapHair` with its own on/off value set in `hairSetup`, plus an entry in `HAIRSTYLES`. Keep `mapHair` free of `if`s: some phone GPUs draw the wrong hair when it branches on the style (the comment above it says more). Keep any new animal generic, not a known mascot.

### Hosting it (GitHub Pages)

Keep `helpercraft.html`, `index.html`, `manifest.webmanifest`, `sw.js`, `.nojekyll`, the `icons/` folder, `README.md` and `LICENSE` at the repository root. In the repo's settings, turn on Pages and serve from the root of the main branch. Your hosted link is then `https://YOUR-USERNAME.github.io/REPO-NAME/`: `index.html` opens the app at once and carries the link preview, and `.nojekyll` makes Pages serve the files as they are. If you fork it, change the addresses in `index.html` to yours.

On that https address, Helpercraft can be added to the Home Screen and opens without internet:
- `manifest.webmanifest` is its name, colours and icons.
- `sw.js` keeps an offline copy of Helpercraft's own files, and nothing else.
- iPhone users get a one-time tip, because Safari deletes a site's saved data after 7 days without a visit, and Home Screen apps don't share Safari's.

The page loads these files only on https (or `localhost`, for the tests). A downloaded file never does. The offline copy refreshes itself: each visit saves the newest files for the next one. If you change the icons or the list of files, bump `CACHE` in `sw.js` (for example `helpercraft-v2`), so everything is fetched fresh.

## Contributing

Contributions are welcome, especially:

- **Role packs reviewed by people who do the job:** nurses, lab staff, teachers, tradespeople. Please say who reviewed each one.
- **Keeping the install steps current** when an app changes its menus or adds skill support.
- **Translations:** more languages, and native speakers checking the Chinese and Spanish (see "Translations" under For builders).

The [contributing guide](CONTRIBUTING.md) has the checks to run and the rules that keep Helpercraft private and simple. Everyone taking part follows the [code of conduct](CODE_OF_CONDUCT.md).

## License

[MIT](LICENSE)
