#!/usr/bin/env python3
"""Evaluation 3's human check (the plan: "I'll rate 20 random pairs myself, blind, on a page that shows them in random
order. My agreement with each judge is reported. It's a check, not the decider.")

    python tests/team_eval_3_rate.py page FILE         # 20 random judged pairs -> a private rating page, and the key
    python tests/team_eval_3_rate.py agree FILE CODE   # the code the page gives back -> agreement with each judge

The 20 pairs are drawn with a fixed seed from every pair a judge compared (the missing-page rule's pairs aren't judged,
so they aren't drawn). Each pair's sides are shuffled, and the page never shows which setup made which answer. The key
(which side is the team folder) stays in tests/results/team-eval-3/human-key.json, private like the answers."""
import base64, html, json, random, re, subprocess, sys
from pathlib import Path
import importlib.util
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('te', ROOT / 'tests' / 'team_eval_3.py'); te = importlib.util.module_from_spec(spec); spec.loader.exec_module(te)
SEED, N = 2026, 20
SHOTS = te.OUT / 'shots'
KEY = te.OUT / 'human-key.json'


def md(text):
    """Markdown as GitHub shows a README (sanitised by GitHub)."""
    body = json.dumps({'text': text, 'mode': 'markdown'})
    return subprocess.run(['gh', 'api', 'markdown', '--input', '-'], input=body, capture_output=True, text=True, encoding='utf-8', check=True).stdout


def show(rec):
    """The same work the judge saw: every message except pure questions, then each file (pages as a picture)."""
    parts = [t['text'].strip() for t in rec['turns'] if t.get('text', '').strip() and not (t.get('waiting') and not t['files'])]
    if not parts and rec['turns']:
        parts = [rec['turns'][-1].get('text', '').strip()]
    out = ''.join(f'<div class="msg">{md(p)}</div>' for p in parts)
    shots = {p['file']: p.get('shot') for p in (rec.get('pages') or [])}
    for f in rec['files']:
        name = html.escape(f['path'])
        if f['path'].lower().endswith(('.html', '.htm')):
            shot = shots.get(Path(f['path']).name)
            img = (f'<img alt="The page {name}, as it opened in a browser" src="data:image/png;base64,{base64.b64encode((SHOTS / shot).read_bytes()).decode()}">'
                   if shot and (SHOTS / shot).exists() else '<p class="note">(No picture of this page.)</p>')
            out += (f'<div class="file"><p class="fname">Page: {name}</p>{img}'
                    f'<details><summary>Show the page\'s code</summary><pre>{html.escape(f["content"][:15000])}</pre></details></div>')
        elif f['path'].lower().endswith('.md'):
            out += f'<div class="file"><p class="fname">File: {name}</p>{md(f["content"])}</div>'
        else:
            out += f'<div class="file"><p class="fname">File: {name}</p><pre>{html.escape(f["content"][:15000])}</pre></div>'
    return out


def page(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    best = te.ok_runs(data)
    judged = sorted({(j['task'], j['vs']) for rows in data['judged'].values() for j in rows if not j.get('auto')})
    rnd = random.Random(SEED)
    picked = rnd.sample(judged, N)
    key, cards = [], []
    for i, (tid, vs) in enumerate(picked):
        c_side = 1 if rnd.random() < 0.5 else 2
        a, b = (best[(tid, 'C')], best[(tid, vs)]) if c_side == 1 else (best[(tid, vs)], best[(tid, 'C')])
        pid = f'p{i + 1:02d}'
        key.append({'id': pid, 'task': tid, 'vs': vs, 'team_folder_is': c_side})
        cards.append(f'''<section class="pair" id="{pid}" hidden>
<p class="count">Pair {i + 1} of {N}</p>
<div class="ask"><p class="label">The request</p>{md(te.TASK[tid]['task'])}</div>
<div class="cols"><article><h2>Answer 1</h2><div class="box">{show(a)}</div></article><article><h2>Answer 2</h2><div class="box">{show(b)}</div></article></div>
<div class="pick" role="group" aria-label="Which answer is better?">
<button type="button" data-v="1">Answer 1 is better</button><button type="button" data-v="0">About the same</button><button type="button" data-v="2">Answer 2 is better</button></div>
</section>''')
        print(pid, 'ready', flush=True)
    KEY.write_text(json.dumps({'results': Path(path).name, 'seed': SEED, 'pairs': key}, indent=1), encoding='utf-8')
    out = te.OUT / 'rate-20.html'
    out.write_text(PAGE.replace('{{CARDS}}', '\n'.join(cards)).replace('{{N}}', str(N)), encoding='utf-8')
    print('page:', out, '| key:', KEY)


def agree(path, code):
    """code: '1102...' one digit per pair (1 or 2 = that answer is better, 0 = about the same)."""
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    key = json.loads(KEY.read_text(encoding='utf-8'))['pairs']
    digits = re.sub(r'\D', '', code)
    assert len(digits) == len(key), f'{len(digits)} answers for {len(key)} pairs'
    mine = {}
    for k, d in zip(key, digits):
        mine[(k['task'], k['vs'])] = 'tie' if d == '0' else ('C' if int(d) == k['team_folder_is'] else 'other')
    out = {'me': {'C': list(mine.values()).count('C'), 'other': list(mine.values()).count('other'), 'tie': list(mine.values()).count('tie')}}
    for judge, rows in data['judged'].items():
        theirs = {(j['task'], j['vs']): j['outcome'] for j in rows}
        both = [k for k in mine if k in theirs]
        out[judge] = {'pairs': len(both), 'same verdict': sum(mine[k] == theirs[k] for k in both),
                      'same winner when neither tied': f"{sum(mine[k] == theirs[k] for k in both if 'tie' not in (mine[k], theirs[k]))} of {sum('tie' not in (mine[k], theirs[k]) for k in both)}"}
    data['human_check'] = {'code': digits, 'key': KEY.name, 'agreement': out}
    te.save(data, Path(path))
    print(json.dumps(out, indent=1))


PAGE = '''<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Blind ratings: {{N}} pairs</title>
<style>
:root { --ink: #231b40; --soft: #5d5485; --line: #e7e2f8; --tint: #f5f2ff; --paper: #fffdfb; }
* { box-sizing: border-box; }
body { margin: 0; color: var(--ink); font: 15.5px/1.55 -apple-system, "Segoe UI", system-ui, sans-serif;
  background: linear-gradient(#bdb4f2, #f1eefb 420px) no-repeat, #f1eefb; }
header, main { max-width: 1240px; margin: 0 auto; padding: 0 16px; }
header { padding-top: 22px; }
h1 { margin: 0 0 6px; font: 700 32px/1.15 "Segoe UI", system-ui, sans-serif; }
.intro { margin: 0 0 14px; max-width: 760px; }
.bar { height: 8px; border-radius: 99px; background: rgba(255,253,251,.7); overflow: hidden; margin: 6px 0 18px; }
.bar i { display: block; height: 100%; width: 0; background: var(--ink); transition: width .2s; }
.count { margin: 0 0 8px; font-weight: 700; color: var(--soft); }
.ask { background: var(--paper); border-radius: 20px; padding: 14px 18px; margin-bottom: 14px; box-shadow: 0 12px 30px -24px rgba(35,27,64,.5); }
.label { margin: 0 0 4px; font-size: 13px; font-weight: 700; letter-spacing: .06em; text-transform: uppercase; color: var(--soft); }
.ask p { margin: 0 0 6px; }
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
article { background: var(--paper); border-radius: 20px; padding: 12px 14px 14px; min-width: 0; box-shadow: 0 12px 30px -24px rgba(35,27,64,.5); }
article h2 { margin: 2px 4px 8px; font-size: 18px; }
.box { max-height: 68vh; overflow: auto; padding: 0 6px; overflow-wrap: anywhere; }
.box table { border-collapse: collapse; margin: 8px 0; font-size: 14px; } .box td, .box th { border: 1px solid var(--line); padding: 4px 8px; vertical-align: top; }
.box pre { white-space: pre-wrap; background: var(--tint); padding: 10px; border-radius: 10px; font-size: 12.5px; }
.box img { max-width: 100%; border: 1px solid var(--line); border-radius: 10px; }
.msg + .msg { border-top: 1px dashed var(--line); margin-top: 10px; padding-top: 6px; }
.file { margin-top: 12px; padding-top: 8px; border-top: 2px solid var(--line); } .fname { font-weight: 700; margin: 0 0 6px; }
.note { color: var(--soft); }
.pick { position: sticky; bottom: 0; display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; padding: 12px 0 16px;
  background: linear-gradient(transparent, #f1eefb 30%); }
.pick button, .nav button, .done button { font: 600 15px "Segoe UI", system-ui, sans-serif; padding: 11px 18px; border-radius: 99px; border: 2px solid var(--ink); background: var(--paper); color: var(--ink); cursor: pointer; }
.pick button[aria-pressed="true"] { background: var(--ink); color: #fff; }
.nav { display: flex; justify-content: space-between; margin: 4px 0 30px; }
.done { background: var(--paper); border-radius: 20px; padding: 18px; margin: 10px 0 40px; }
.done code { display: block; font-size: 20px; letter-spacing: .12em; margin: 10px 0; word-break: break-all; }
:focus-visible { outline: 3px solid var(--ink); outline-offset: 2px; }
@media (max-width: 760px) { .cols { grid-template-columns: 1fr; } .box { max-height: none; } h1 { font-size: 26px; } }
</style></head>
<body>
<header><h1>Blind ratings: {{N}} pairs</h1>
<p class="intro">Each pair is two answers to the same request, in random order, with nothing to say which setup made which. Pick the one you'd rather use, or "About the same". Judge the finished work. Your picks are kept in this browser, so you can stop and come back. At the end, copy the code and send it to me.</p>
<div class="bar" aria-hidden="true"><i></i></div></header>
<main>
{{CARDS}}
<div class="nav"><button type="button" id="prev">Previous pair</button><button type="button" id="next">Next pair</button></div>
<section class="done" id="done" hidden><h2>Done</h2><p>Your code (one digit per pair):</p><code id="code"></code>
<button type="button" id="copy">Copy the code</button> <span id="copied" aria-live="polite"></span></section>
</main>
<script>
const pairs = [...document.querySelectorAll('.pair')], N = pairs.length;
let picks = {}; try { picks = JSON.parse(localStorage.getItem('ratings') || '{}'); } catch (e) {}
let at = 0;
function save() { try { localStorage.setItem('ratings', JSON.stringify(picks)); } catch (e) {} }
function render() {
  pairs.forEach((p, i) => { p.hidden = i !== at; p.querySelectorAll('.pick button').forEach(b => b.setAttribute('aria-pressed', picks[p.id] === b.dataset.v)); });
  const done = Object.keys(picks).length;
  document.querySelector('.bar i').style.width = (100 * done / N) + '%';
  document.getElementById('prev').disabled = at === 0;
  document.getElementById('next').textContent = at === N - 1 ? 'Finish' : 'Next pair';
  const all = pairs.every(p => picks[p.id] !== undefined);
  document.getElementById('done').hidden = !all;
  document.getElementById('code').textContent = all ? pairs.map(p => picks[p.id]).join('') : '';
  window.scrollTo(0, 0);
}
document.querySelectorAll('.pick button').forEach(b => b.addEventListener('click', () => {
  picks[b.closest('.pair').id] = b.dataset.v; save();
  if (at < N - 1) at++;
  render();
}));
document.getElementById('prev').onclick = () => { if (at > 0) { at--; render(); } };
document.getElementById('next').onclick = () => { if (at < N - 1) { at++; render(); } else render(); };
document.getElementById('copy').onclick = async () => {
  const t = document.getElementById('code').textContent;
  try { await navigator.clipboard.writeText(t); document.getElementById('copied').textContent = 'Copied.'; }
  catch (e) { document.getElementById('copied').textContent = 'Select the code and copy it.'; }
};
render();
</script>
</body></html>'''

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'page' and len(sys.argv) == 3:
        page(sys.argv[2])
    elif cmd == 'agree' and len(sys.argv) == 4:
        agree(sys.argv[2], sys.argv[3])
    else:
        print(__doc__)
