# Contributing to Helpercraft

Thank you for helping. These help most right now:

- **Job packs reviewed by people who do the job.** Nurses, lab staff, teachers and tradespeople can check a job's tasks, rules and hand-over triggers. Please say who reviewed each one.
- **Install steps kept current** when an AI app changes its menus or adds skill support.
- **Translations:** new languages, and native speakers checking the Chinese and Spanish.
- **Bug reports** with your browser, device and steps. Screenshots help.

For anything bigger than a small fix, please open an issue first to agree on the approach.

## How Helpercraft is built

Helpercraft is one file, `helpercraft.html`, with no build step and no dependencies. Open it in a browser and edit it in any text editor.

- **The agent file:** at the top, the name and a description of 200 characters or fewer, saying what the agent does and when to use it; that's what an AI reads to decide. Below come the role, working style, tasks, rules and hand-over points. Personality, animal, MBTI type and star sign sit in a short section at the end and never override the rules.
- **Layout:** `App` holds the data tables (`ROLES`, `SPECIES`, `HAIRSTYLES`, `ARCHETYPES`, `MBTI_AXES`, `ZODIAC`, `HABITS`, `LICENSE_LIST`), the file generator (`buildSkill`), a small zip writer, Agent home storage (one key per agent plus an index) and the interface. `Stage` is the 3D view.
- **Add a job:** add one entry to `ROLES`. Give every task a topic in the same position in `topics`, and each job title 2–3 pre-ticked tasks in `picks`; the self-test checks both. Reuse a costume through `look.acc` (0–10) and `look.pattern` (0–7), so no 3D work is needed.
- **Translations:** English text is the key. The Chinese and Spanish live in the page's `<script id="i18n">` block, and code asks for text with `T('English text', { name })`. `python tests/i18n.py keys` lists every text and where it's used; `python tests/i18n.py sample zh` prints a whole agent in one language.

### The 3D view

- `Stage` draws every kind of agent in one WebGL2 fragment shader, from simple shapes (ray marching), with no libraries. The scene is sampled from one loop, so the GPU driver compiles it once. The compile runs in the background, and the view adapts its resolution to stay smooth. `Stage.portrait()` draws the Agent home portraits.
- `?nogl` turns the 3D view off. On a computer too slow for it (under about 10 frames a second at the lowest sharpness, for 5 seconds), the character stands still and is redrawn only when something changes; the browser remembers this for 7 days. `?still` forces it, and `?still=off` never switches (the tests use that).
- **Add an animal or a hairstyle:** an animal is a branch in the shader's `mapHead` plus an entry in `SPECIES`. A hairstyle is a new part in `mapHair`, with its own on/off value set in `hairSetup`, plus an entry in `HAIRSTYLES`. Follow the two shader rules below.

### Hosting (GitHub Pages)

Keep `helpercraft.html`, `index.html`, `manifest.webmanifest`, `sw.js`, `.nojekyll`, `icons/`, `README.md` and `LICENSE` at the repository root, and serve Pages from the root of the main branch. `index.html` opens the app and carries the link preview; if you fork, change its addresses to yours. `.nojekyll` makes Pages serve the files as they are.

On https (or `localhost`), Helpercraft can be added to the Home Screen and opens offline. `manifest.webmanifest` gives its name and icons, and `sw.js` keeps an offline copy of Helpercraft's own files, nothing else. Each visit saves the newest files for the next one; if you change the icons or the file list, bump `CACHE` in `sw.js`. iPhone users get a one-time tip, because Safari can clear a site's data after 7 days without a visit, and Home Screen apps keep their own.

## Checks to run

- **Self-test:** open `helpercraft.html#test`; every check should pass. It covers names, YAML quoting, every job and job title, the portable file and the Claude app zip, builder extras, zip structure, saved and restored agents, the team folder, and a byte-for-byte guard on the default file. Opened from a file, it skips the 5 folder checks, which need the browser's private test folder.
- **Translations:** the self-test fails if a text is missing its Chinese or Spanish, or a `{placeholder}`. To edit translations, run `python tests/i18n.py pull`, edit `tests/out/i18n/zh.json` or `es.json`, then run `python tests/i18n.py check` (it should report no problems) and `python tests/i18n.py merge`.
- **End-to-end tests:** `python tests/e2e.py` clicks through Helpercraft as a person would, in Chrome, Edge, Chromium, Firefox and WebKit, at phone, tablet and computer sizes, in all three languages, opened as a file and from a local server, plus stress, broken-input and security tests. Setup and commands are in the README's [For builders](README.md#for-builders) section. Everything stays on your computer.

## Rules that keep Helpercraft what it is

- **Nothing leaves the device.** No network requests, analytics, accounts or third-party scripts. Keep the Content-Security-Policy as it is.
- **One file.** A downloaded `helpercraft.html` must keep working on its own.
- **No device checks.** Fix problems for everyone, not for one phone or browser by name.
- **Every text goes through `T()`**, with its Chinese and Spanish added.
- **Keep the shader's `mapHair` free of `if`s.** Some phone GPUs draw the wrong hair when it branches on the style (the comment above it explains).
- **New animals stay generic**, never a known mascot or character.
- **Plain, precise words.** Write for readers who may not code, without talking down to anyone.

## Pull requests

- Keep each one to a single change, and say what it does and why.
- For anything visible, add before-and-after screenshots.
- Run the checks above and say which ones you ran.

By contributing, you agree that your work is shared under the project's [MIT license](LICENSE). Please follow the [code of conduct](CODE_OF_CONDUCT.md).
