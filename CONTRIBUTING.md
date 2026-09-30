# Contributing to Helpercraft

Thank you for helping. These help most right now:

- **Role packs reviewed by people who do the job.** Nurses, lab staff, teachers and tradespeople can check a job's tasks, rules and hand-over triggers. Please say who reviewed each one.
- **Keeping the install steps current** when an AI app changes its menus or adds skill support.
- **Translations.** New languages, and native speakers checking the Chinese and Spanish.
- **Bug reports** with your browser, device and what you did. Screenshots help.

For anything bigger than a small fix, open an issue first so we can agree on the approach.

## How Helpercraft is built

Helpercraft is one file, `helpercraft.html`, with no build step and no dependencies. Open it in a browser, and edit it in any text editor. The README's [For builders](README.md#for-builders) section explains how the file is laid out and how to add a job.

## Checks to run

- **Self-test:** open `helpercraft.html#test` in a browser. Every check should pass.
- **Translations:** the self-test fails if any text is missing its Chinese or Spanish. If you edit translations, run `python tests/i18n.py pull`, edit `tests/out/i18n/zh.json` or `es.json`, then run `python tests/i18n.py check` (it should report no problems) and `python tests/i18n.py merge`.
- **End-to-end tests:** set up once with `pip install playwright pyyaml pillow` and `python -m playwright install chromium firefox webkit`. Then `python tests/e2e.py --tiers A --rounds 1 --engines chrome` is a quick run of a few minutes, and `python tests/e2e.py` runs everything in 5 browsers (about 45 minutes; it also needs Google Chrome and Microsoft Edge installed). Everything stays on your computer.

## Rules that keep Helpercraft what it is

- **Nothing leaves the device.** No network requests, analytics, accounts or third-party scripts. Keep the Content-Security-Policy as it is.
- **One file.** A downloaded `helpercraft.html` must keep working on its own.
- **No device checks.** Fix problems for everyone, not for one phone or browser by name.
- **Every text goes through `T()`**, with its Chinese and Spanish added. The self-test fails if a translation or a `{placeholder}` is missing.
- **Keep the shader's `mapHair` free of `if`s.** Some phone GPUs draw the wrong hair when it branches on the style (the comment above it explains).
- **New animals stay generic**, never a known mascot or character.
- **Plain words.** Helpercraft is for people who've never written code, so write the way you'd explain it to a friend.

## Pull requests

- Keep each one to a single change, and say what it does and why.
- For anything visible, add before-and-after screenshots.
- Run the checks above and say which ones you ran.

By contributing, you agree that your work is shared under the project's [MIT license](LICENSE). Please follow the [code of conduct](CODE_OF_CONDUCT.md).
