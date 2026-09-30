#!/usr/bin/env python3
"""Translations for helpercraft.html. English is the key; Traditional Chinese (zh) and Spanish (es) live in the page's
<script id="i18n"> block as {"English": ["中文", "Español"]}.

    python tests/i18n.py keys              # every text and where it appears -> tests/out/i18n/keys.json
    python tests/i18n.py check zh.json     # is every text translated, with the same {placeholders}?
    python tests/i18n.py merge             # tests/out/i18n/zh.json + es.json -> the page (or: merge --into copy.html)
    python tests/i18n.py sample zh         # a whole agent, its file and its team note, in that language
    python tests/i18n.py pull              # the page's translations -> tests/out/i18n/zh.json + es.json, to edit

Needs Playwright (see tests/e2e.py). Nothing leaves this computer.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'helpercraft.html'
DIR = ROOT / 'tests' / 'out' / 'i18n'
BLOCK = re.compile(r'(<script id="i18n" type="application/json">)(.*?)(</script>)', re.S)


def holes(s):   # {placeholders}; {a} is the English "a/an", which other languages leave out
    return sorted(x for x in re.findall(r'\{\w+\}', s) if x != '{a}')


def page_eval(page_path, js, arg=None):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, channel='chrome')
        p = b.new_page()
        p.goto(Path(page_path).resolve().as_uri())
        p.wait_for_function('() => window.Helpercraft && Helpercraft.i18nKeys')
        out = p.evaluate(js, arg)
        b.close()
        return out


def keys():
    rows = page_eval(PAGE, '() => [...Helpercraft.i18nKeys()].map(([key, where]) => ({ key, where }))')
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / 'keys.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(rows)} texts -> {DIR / "keys.json"}')
    return rows


def check(path):
    rows = json.loads((DIR / 'keys.json').read_text(encoding='utf-8'))
    tr = json.loads(Path(path).read_text(encoding='utf-8'))
    want = [r['key'] for r in rows]
    problems = [f'missing: {k!r}' for k in want if not (isinstance(tr.get(k), str) and tr[k].strip())]
    problems += [f'extra: {k!r}' for k in tr if k not in set(want)]
    for k in want:
        t = tr.get(k)
        if isinstance(t, str) and t.strip() and holes(t) != holes(re.sub(r'\|\w+$', '', k)):
            problems.append(f'placeholders differ: {k!r} -> {t!r}')
    for p in problems:
        print(p)
    print(f'{path}: {len(want) - len([p for p in problems if p.startswith("missing")])}/{len(want)} translated, {len(problems)} problems')
    return not problems


def merge(into=PAGE):
    zh = json.loads((DIR / 'zh.json').read_text(encoding='utf-8'))
    es = json.loads((DIR / 'es.json').read_text(encoding='utf-8'))
    rows = json.loads((DIR / 'keys.json').read_text(encoding='utf-8'))
    table = {r['key']: [zh[r['key']], es[r['key']]] for r in rows if r['key'] in zh and r['key'] in es}
    body = json.dumps(table, ensure_ascii=False, indent=0).replace('</', '<\\/')
    text = PAGE.read_text(encoding='utf-8')
    if not BLOCK.search(text):
        sys.exit('no <script id="i18n"> block in the page')
    Path(into).write_text(BLOCK.sub(lambda m: m.group(1) + body + m.group(3), text, count=1), encoding='utf-8', newline='\n')
    print(f'{len(table)} translations -> {into}')


def pull():
    table = json.loads(BLOCK.search(PAGE.read_text(encoding='utf-8')).group(2))
    DIR.mkdir(parents=True, exist_ok=True)
    for i, lang in enumerate(['zh', 'es']):
        (DIR / f'{lang}.json').write_text(json.dumps({k: v[i] for k, v in table.items()}, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(table)} translations -> {DIR}')


SAMPLE_JS = """lang => {
  Helpercraft.setLang(lang);
  const S = Helpercraft.state, keep = JSON.parse(JSON.stringify(S)), out = [];
  const agents = [
    { name: 'Pip', role: 'health', specialty: 'Nurse agent', archetype: 'mentor', look: { ...S.look, species: 'dog' }, habits: ['clarify', 'plan', 'check', 'next', 'first', 'flow', 'plain'], invoke: 'manual', mbti: { ei: 'I', sn: 'N', tf: 'F', jp: 'P' }, zodiac: 'leo', needs: ['internet'] },
    { name: 'Remy', role: 'tech', specialty: 'Coding buddy', archetype: 'cheeky', emoji: true, catchphrase: 'Ship it!' },
    { name: 'Luna', role: 'custom', customTitle: '', customTasks: ['Answer booking questions', 'Send reminders'], archetype: 'carer', mbti: { ei: 'E', sn: null, tf: null, jp: 'J' } },
  ];
  for (const h of agents) {
    Object.assign(S, JSON.parse(JSON.stringify(keep)), { tasks: null, roleRules: null, handoff: null, exampleAsk: null, exampleReply: null }, h);
    const traits = { sunny: [85, 80, 55, 40], mentor: [70, 25, 20, 75], cheeky: [70, 90, 90, 30], carer: [95, 25, 15, 50] }[h.archetype];
    S.traits = { warmth: traits[0], energy: traits[1], humor: traits[2], detail: traits[3] };
    const sk = Helpercraft.buildSkill();
    out.push(`===== ${h.name} (${h.role}) =====`, sk.text, ...sk.files.map(([p, t]) => `----- ${p} -----\\n${t}`));
  }
  Object.assign(S, keep);
  return out.join('\\n');
}"""


def sample(lang, page=PAGE):
    print(page_eval(page, SAMPLE_JS, lang))


if __name__ == '__main__':
    cmd, *rest = sys.argv[1:] or ['help']
    if cmd == 'keys':
        keys()
    elif cmd == 'check':
        sys.exit(0 if all([check(DIR / f if '/' not in f and '\\' not in f else f) for f in rest or ['zh.json', 'es.json']]) else 1)
    elif cmd == 'merge':
        merge(rest[1] if rest[:1] == ['--into'] else PAGE)
    elif cmd == 'pull':
        pull()
    elif cmd == 'sample':
        sample(rest[0] if rest else 'zh', rest[1] if len(rest) > 1 else PAGE)
    else:
        print(__doc__)
