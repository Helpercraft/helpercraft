#!/usr/bin/env python3
"""Team-folder evaluation: does Claude Code use a Helpercraft team the way the README says?

Compares the team folder ("active": the AI reads START-HERE.md, suggests helpers and asks first) with the same helpers
installed as Claude Code skills ("passive": the tool picks a skill by itself). The plan and scoring rules, written
before the full run, are in tests/team_eval.md.

    python tests/team_eval.py --pilot     # 2 tasks x 1 run in both modes, plus one squeeze test
    python tests/team_eval.py             # 10 tasks x 3 runs x 2 modes, plus 3 squeeze tests x 3 runs x 2 modes

Needs the Claude Code CLI, signed in. Every run is read-only (Read, Glob, Grep, Skill) and uses your plan's usage.
Raw results go to tests/out/team-eval/ (stays on this computer)."""
import argparse, concurrent.futures as cf, datetime, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = ROOT / 'tests' / 'fixtures' / 'sample-team'
# a short folder: Windows can't start programs from a working folder with a very long path
WORK = Path(os.environ.get('TEAM_EVAL_WORK') or Path(os.environ.get('TEMP', '/tmp')) / 'hce')
OUT = ROOT / 'tests' / 'out' / 'team-eval'
CLEAN = ['--setting-sources', 'project', '--strict-mcp-config']   # no user hooks, plugins, MCP servers or settings
DIRS = {'clover': 'clover-nurse-helper', 'mochi': 'mochi-support-agent', 'luna': 'luna-ui-designer', 'taro': 'taro-maintenance-tech',
        'pip': 'pip-cafe-assistant', 'remy': 'remy-coding-buddy', 'nova': 'nova-tutor', 'otto': 'otto-lab-technician'}
ALL = set(DIRS)
COPY = 'My helper team is in {team}. Read START-HERE.md there first, then suggest which of my helpers should work on my task, and wait for my OK.'
# name, task, at least one of these must be picked (empty: nothing should be), must not be picked
TASKS = [
    ('review', 'A customer left a one-star review saying their latte was cold and the barista was rude. Help me reply.', {'mochi'}, ALL - {'mochi', 'pip'}),
    ('medical', "Explain what 'tachycardia' means in plain words for a patient leaflet.", {'clover'}, ALL - {'clover', 'nova'}),
    ('website', 'Build a simple one-page website for my café, with our menu and opening hours.', {'pip', 'remy', 'luna'}, {'clover', 'mochi', 'taro', 'nova', 'otto'}),
    ('bug', "My Python script stops with KeyError: 'price'. What does that mean and how do I fix it?", {'remy'}, ALL - {'remy', 'nova'}),
    ('machine', "Our espresso machine shows error E23 and won't heat up. What should I check first?", {'taro'}, ALL - {'taro', 'pip'}),
    ('design', "Is dark blue text on a black background OK for my app's login screen? Be honest.", {'luna'}, ALL - {'luna', 'remy'}),
    ('homework', 'Help my 10-year-old understand adding fractions like 1/4 + 1/3, step by step.', {'nova'}, ALL - {'nova'}),
    ('lab', 'How do I make 100 mL of a 1:50 dilution from a 2 M stock solution?', {'otto'}, ALL - {'otto', 'nova'}),
    ('bakesale', "Plan the menu and a sign-up web page for our café's charity bake sale.", {'pip', 'remy', 'luna'}, {'clover', 'taro', 'otto'}),
    ('none', 'Suggest a relaxed three-day itinerary for a first trip to Kyoto.', set(), ALL),
]
SQUEEZE = [('review', 'mochi', 'Mochi'), ('bug', 'remy', 'Remy'), ('design', 'luna', 'Luna')]
PROBE = 'Quick check before we go on: which helper are you working as right now? Name them and quote two of their rules.'
JUDGE = '''You grade an AI assistant's reply. Answer with JSON only, no other text.
The user has these helpers: clover (nurse helper), mochi (support agent), luna (UI designer), taro (maintenance tech),
pip (café assistant), remy (coding buddy), nova (tutor), otto (lab technician).

The reply:
<<<
{text}
>>>

Return {{"suggested": [helpers the reply proposes to use for the task], "rejected": [helpers it says don't fit or won't use],
"asked_before_starting": true if it asks the user to confirm or choose before doing the task,
"did_the_task": true if the reply already contains the finished work (the drafted reply, the explanation, the code, the page or the plan)}}.
Use only the lowercase names above.'''
PROBE_JUDGE = '''Answer with JSON only, no other text. An AI assistant was asked which helper it is working as, and to quote two of that helper's rules.

Its reply:
<<<
{text}
>>>

That helper's actual file:
<<<
{skill}
>>>

Return {{"named": "the helper it says it is working as, lowercase first name, or none", "rules_from_file": how many of the quoted rules (0, 1 or 2) say the same as a rule in the file}}.'''


def setup():
    shutil.rmtree(WORK, ignore_errors=True)
    shutil.copytree(FIX, WORK / 'team')
    (WORK / 'active').mkdir(); (WORK / 'judge').mkdir()
    for n, d in DIRS.items():
        (WORK / 'passive' / '.claude' / 'skills' / d).mkdir(parents=True)
        shutil.copy(FIX / 'helpers' / d / 'SKILL.md', WORK / 'passive' / '.claude' / 'skills' / d / 'SKILL.md')


def claude(cwd, prompt, resume=None, add_dir=None, model=None, tools='Read,Glob,Grep,Skill', timeout=480):
    cmd = ['claude', '-p', prompt, '--output-format', 'stream-json', '--verbose', *CLEAN]
    if resume: cmd += ['--resume', resume]
    if add_dir: cmd += ['--add-dir', str(add_dir)]
    if model: cmd += ['--model', model]
    cmd += ['--tools', tools]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    except subprocess.TimeoutExpired:
        return {'error': 'timeout', 'secs': round(time.time() - t0)}
    events = []
    for line in p.stdout.splitlines():
        if line.startswith('{'):
            try: events.append(json.loads(line))
            except ValueError: pass
    used = [(c['name'], c.get('input', {})) for e in events if e.get('type') == 'assistant'
            for c in e['message'].get('content', []) if c.get('type') == 'tool_use']
    res = next((e for e in events if e.get('type') == 'result'), {})
    init = next((e for e in events if e.get('subtype') == 'init'), {})
    return {'session': res.get('session_id') or init.get('session_id'), 'text': res.get('result') or '', 'tools': used,
            'error': ('error: ' + (p.stderr or '')[-200:]) if (res.get('is_error') or not res) else None, 'secs': round(time.time() - t0),
            'version': init.get('claude_code_version'), 'model': init.get('model'),
            'squeezed': any(e.get('subtype') == 'compact_boundary' for e in events)}


def judge(template, **kw):
    r = claude(WORK / 'judge', template.format(**kw), model='haiku', tools='')
    m = re.search(r'\{.*\}', r.get('text') or '', re.S)
    try:
        return json.loads(m.group(0)) if m else None
    except ValueError:
        return None


def rel(path):   # tool paths relative to the work folder, so nothing personal ends up in reports
    path = str(path).replace('\\', '/')
    if '/.claude/projects/' in path:   # Claude Code's saved copy of the conversation (its summary links to it after /compact)
        return 'saved-conversation.jsonl'
    return path.split('/hce/')[-1]


def reads(r):
    return [rel(i.get('file_path', '')) for n, i in r.get('tools', []) if n == 'Read']


def skills_called(r):
    return {n for n, d in DIRS.items() for t, i in r.get('tools', []) if t == 'Skill' and d in str(i.get('skill', ''))}


def came_back(sid, mode, key):
    """Right after /compact, did Claude Code put the helper's own rules back in view? Read from its saved session (None if not found)."""
    f = Path.home() / '.claude' / 'projects' / re.sub(r'[^A-Za-z0-9]', '-', str(WORK / mode)) / f'{sid}.jsonl'
    if not sid or not f.exists():
        return None
    files = {d: (FIX / 'helpers' / d / 'SKILL.md').read_text(encoding='utf-8') for d in DIRS.values()}
    own = [l[2:] for l in files[DIRS[key]].splitlines() if l.startswith('- ') and not any(l in t for d, t in files.items() if d != DIRS[key])]
    def text(o):
        return o if isinstance(o, str) else '\n'.join(text(v) for v in (o.values() if isinstance(o, dict) else o if isinstance(o, list) else []))
    after = False
    for e in (json.loads(l) for l in f.read_text(encoding='utf-8').splitlines() if l.strip()):
        if e.get('subtype') == 'compact_boundary':
            after = True
        elif after and e.get('type') == 'attachment' and any(r in text(e) for r in own):
            return True
        elif after and e.get('type') == 'user' and PROBE in text(e):   # reached the probe: nothing came back
            return False
    return False


def part1(task, mode, rep):
    name, text, need, never = next(t for t in TASKS if t[0] == task)
    if mode == 'active':
        r = claude(WORK / 'active', COPY.format(team=WORK / 'team') + '\n\nMy task: ' + text, add_dir=WORK / 'team')
    else:
        r = claude(WORK / 'passive', text)
    out = {'part': 1, 'task': name, 'mode': mode, 'rep': rep, 'secs': r.get('secs'), 'error': r.get('error'),
           'version': r.get('version'), 'model': r.get('model'), 'reads': reads(r), 'skills': sorted(skills_called(r)), 'reply': r.get('text', '')}
    if r.get('error'):
        return out
    g = judge(JUDGE, text=r['text']) or {}
    picked = set(g.get('suggested') or []) & ALL if mode == 'active' else skills_called(r)
    out.update(judge=g, picked=sorted(picked),
               asked_first=bool(g.get('asked_before_starting')) and not g.get('did_the_task'),   # a question after finished work isn't asking first
               correct=(not picked) if not need else bool(picked & need) and not (picked & never),
               read_start_here=any(p.endswith('START-HERE.md') for p in out['reads']),
               opened_helper_first=any('/SKILL.md' in p and 'helpers/' in p for p in out['reads']))
    return out


def part2(task, key, helper, mode, rep):
    text = next(t[1] for t in TASKS if t[0] == task)
    skill = (FIX / 'helpers' / DIRS[key] / 'SKILL.md').read_text(encoding='utf-8')
    steps, cwd, extra = [], WORK / mode, {'add_dir': WORK / 'team'} if mode == 'active' else {}
    def step(label, prompt, resume):
        r = claude(cwd, prompt, resume=resume, **extra)
        steps.append({'step': label, 'secs': r.get('secs'), 'error': r.get('error'), 'reads': reads(r), 'skills': sorted(skills_called(r)),
                      'squeezed': r.get('squeezed'), 'reply': r.get('text', '')})
        return r
    if mode == 'active':
        s = step('task', COPY.format(team=WORK / 'team') + '\n\nMy task: ' + text, None)
        sid = s.get('session')
        if sid: step('ok', f'OK, go with {helper}.', sid)
    else:
        s = step('task', text, None); sid = s.get('session')
    out = {'part': 2, 'task': task, 'helper': key, 'mode': mode, 'rep': rep, 'steps': steps, 'session': sid}
    if not sid or any(x['error'] for x in steps):
        out['error'] = 'setup failed'; return out
    step('squeeze', '/compact', sid)
    p1 = step('probe', PROBE, sid)
    step('call back', COPY.format(team=WORK / 'team') + f' Keep going with {helper}.' if mode == 'active' else '/' + DIRS[key], sid)
    p2 = step('probe again', PROBE, sid)
    if any(x['error'] for x in steps):
        out['error'] = 'a step failed'; return out
    j1, j2 = judge(PROBE_JUDGE, text=p1['text'], skill=skill) or {}, judge(PROBE_JUDGE, text=p2['text'], skill=skill) or {}
    kept = lambda j: str(j.get('named', '')).lower().startswith(key) and (j.get('rules_from_file') or 0) >= 1
    out.update(squeezed=any(x['squeezed'] for x in steps), judge_after=j1, judge_back=j2, kept_after_squeeze=kept(j1), kept_after_call_back=kept(j2),
               reread_to_answer=any('SKILL.md' in p for p in reads(p1)), came_back=came_back(sid, mode, key),
               read_in_place=mode == 'active' and any(f'helpers/{DIRS[key]}/SKILL.md' in p for x in steps if x['step'] == 'ok' for p in x['reads']))
    return out


def counts(results):
    """The numbers the report shows: counts out of the runs that finished (errors and timeouts counted apart)."""
    c = {}
    need = {t[0]: (t[2], t[3]) for t in TASKS}
    def strict(r):   # the plan's first wording: every helper that fits is picked, and none that must not be
        fit, never = need[r['task']]
        picked = set(r['picked'])
        return fit <= picked and not picked & never if fit else not picked
    for mode in ('active', 'passive'):
        p1 = [r for r in results if r.get('part') == 1 and r.get('mode') == mode]
        ok1 = [r for r in p1 if not r.get('error')]
        p2 = [r for r in results if r.get('part') == 2 and r.get('mode') == mode]
        ok2 = [r for r in p2 if not r.get('error')]
        multi = [len(r['picked']) for r in ok1 if r['task'] in ('website', 'bakesale')]
        c[mode] = {'right': sum(bool(r['correct']) for r in ok1), 'runs1': len(ok1), 'errors1': len(p1) - len(ok1),
                   'asked': sum(bool(r.get('asked_first')) for r in ok1), 'did_task': sum(bool((r.get('judge') or {}).get('did_the_task')) for r in ok1),
                   'kept': sum(bool(r['kept_after_squeeze']) for r in ok2), 'back': sum(bool(r['kept_after_call_back']) for r in ok2),
                   'reread': sum(bool(r.get('reread_to_answer')) for r in ok2), 'runs2': len(ok2), 'errors2': len(p2) - len(ok2),
                   'multi': (sum(multi) / len(multi)) if multi else 0,
                   'start': sum(bool(r.get('read_start_here')) for r in ok1), 'first': sum(bool(r.get('opened_helper_first')) for r in ok1),
                   'in_place': sum(bool(r.get('read_in_place')) for r in ok2), 'strict': sum(strict(r) for r in ok1),
                   # noticed after the full run, not pre-set scores: what came back after the squeeze, and how the first probe was answered
                   'came_back': sum(bool(r.get('came_back')) for r in ok2),
                   'looked_back': sum(any(rel(x) == 'saved-conversation.jsonl' for x in st['reads']) for r in ok2 for st in r['steps'] if st['step'] == 'probe'),
                   'from_memory': sum(not st['reads'] for r in ok2 for st in r['steps'] if st['step'] == 'probe')}
        c[mode]['tasks'] = {t[0]: (sum(bool(r['correct']) for r in ok1 if r['task'] == t[0]), sum(1 for r in ok1 if r['task'] == t[0]),
                                   sorted({h for r in ok1 if r['task'] == t[0] for h in r['picked']})) for t in TASKS}
    return c


CHART = '''<!doctype html><html><head><meta charset="utf-8"><style>
body {{ margin: 0; background: {bg}; color: {ink}; font: 16px/1.4 "Segoe UI", system-ui, sans-serif; }}
.box {{ width: 600px; padding: 24px 26px 22px; box-sizing: border-box; }}   /* narrow, so phones shrink it less */
h3 {{ margin: 0; font-size: 21px; line-height: 1.25; }} h3 span {{ display: block; font-size: 15px; font-weight: 600; color: {soft}; margin-top: 2px; }}
.sub {{ color: {soft}; font-size: 14px; margin: 6px 0 14px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 15px; margin-bottom: 12px; }} .legend i {{ display: inline-block; width: 13px; height: 13px; border-radius: 3px; margin-right: 6px; vertical-align: -1px; }}
.m {{ margin: 14px 0 16px; }} .m b {{ display: block; font-size: 16.5px; line-height: 1.3; margin-bottom: 6px; }}
.row {{ display: grid; grid-template-columns: 1fr 78px; align-items: center; gap: 10px; margin: 4px 0; }}
.track {{ height: 16px; background: {track}; border-radius: 4px; overflow: hidden; }} .bar {{ height: 100%; border-radius: 4px; }}
.n {{ font-size: 15.5px; color: {ink}; font-variant-numeric: tabular-nums; }}
.note {{ margin-top: 16px; padding-top: 12px; border-top: 1px solid {track}; font-size: 14px; color: {soft}; }}
</style></head><body><div class="box">
<h3>With and without a Helpercraft team folder<span>Test of {date}</span></h3>
<p class="sub">Same 8 helpers, same tasks, tested with Claude Code. More AI agents and models are planned. Counts out of the runs that finished.</p>
<div class="legend"><span><i style="background:{c1}"></i>With the team folder</span><span><i style="background:{c2}"></i>Without: the same helpers as installed skills</span></div>
{rows}
<div class="note">{note}</div>
</div></body></html>'''


def chart(c, date, theme):
    pal = {'light': dict(bg='#ffffff', ink='#1f2328', soft='#59636e', track='#eef0f3', c1='#6c5ce7', c2='#e8894a'),
           'dark': dict(bg='#0d1117', ink='#f0f6fc', soft='#9198a1', track='#262c36', c1='#9085e9', c2='#d95926')}[theme]
    def metric(label, key, total):
        rows = ''.join(f'<div class="row"><div class="track"><div class="bar" style="width:{100 * c[m][key] / max(1, c[m][total]):.1f}%;background:{pal[col]}"></div></div>'
                       f'<span class="n">{c[m][key]} of {c[m][total]}</span></div>' for m, col in (('active', 'c1'), ('passive', 'c2')))
        return f'<div class="m"><b>{label}</b>{rows}</div>'
    rows = metric('Picked the right helper for the task', 'right', 'runs1') + metric('Asked before starting (by design)', 'asked', 'runs1') \
        + metric('Still knew its helper after the chat was shortened', 'kept', 'runs2') \
        + metric("Helper's rules put back in view after the chat was shortened (found in the logs)", 'came_back', 'runs2') \
        + metric('Back to the helper after one step', 'back', 'runs2')
    note = (f'By design: START-HERE.md asks the AI to suggest helpers and wait for an OK. Found in the logs, not a pre-set score: after the chat was shortened, '
            f'the installed-skill AI dug through its saved copy of the old conversation before answering {c["passive"]["looked_back"]} of '
            f'{c["passive"]["runs2"]} times. For the two-part tasks the team folder proposed {c["active"]["multi"]:.1f} helpers on average, '
            f'installed skills {c["passive"]["multi"]:.1f}.')
    return agents(CHART.format(rows=rows, note=note, date=date, **pal))


def report(path):
    results = json.loads(Path(path).read_text(encoding='utf-8'))
    c = counts(results)
    ver = next((r.get('version') for r in results if r.get('version')), '?')
    model = next((r.get('model') for r in results if r.get('model')), '?')
    date = datetime.date.fromtimestamp(Path(path).stat().st_mtime).strftime('%-d %B %Y') if os.name != 'nt' else datetime.date.fromtimestamp(Path(path).stat().st_mtime).strftime('%#d %B %Y')
    from playwright.sync_api import sync_playwright
    img = ROOT / 'docs' / 'readme'
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for theme in ('light', 'dark'):
            p = b.new_page(viewport={'width': 600, 'height': 400}, device_scale_factor=2)
            p.set_content(chart(c, date, theme)); p.wait_for_timeout(200)
            p.locator('.box').screenshot(path=str(img / f'eval-{theme}.png'))
        b.close()
    data = ROOT / 'tests' / 'results' / f'team-eval-{datetime.date.fromtimestamp(Path(path).stat().st_mtime).isoformat()}.json'
    data.parent.mkdir(exist_ok=True)
    keep = ('part', 'task', 'helper', 'mode', 'rep', 'picked', 'correct', 'asked_first', 'reads', 'skills', 'read_start_here', 'opened_helper_first',
            'squeezed', 'kept_after_squeeze', 'kept_after_call_back', 'reread_to_answer', 'read_in_place', 'came_back', 'judge', 'judge_after', 'judge_back', 'error')
    pub = []
    for r in results:
        q = {k: r[k] for k in keep if k in r}
        if 'reads' in q: q['reads'] = [rel(x) for x in q['reads']]
        if 'reply' in r: q['reply'] = clean(r['reply'])
        if 'steps' in r: q['steps'] = [{'step': x['step'], 'reads': [rel(y) for y in x.get('reads', [])], 'skills': x.get('skills', []),
                                        'squeezed': x.get('squeezed'), 'reply': clean(x.get('reply', ''))} for x in r['steps']]
        pub.append(q)
    data.write_text(json.dumps({'tool': f'Claude Code {ver}', 'model': model, 'date': date, 'runs': pub}, ensure_ascii=False, indent=1), encoding='utf-8')
    write_md(results, c, ver, model, date)
    json.dump(c, sys.stdout, indent=1, default=list)
    return c, ver, model, date


def agents(s):   # the app renamed "helper" to "agent" on 30 Sep 2026; the report's own words follow, the test's prompts don't
    s = re.sub(r'\b([Aa]) helper\b', lambda m: ('An' if m.group(1) == 'A' else 'an') + ' agent', s)
    for a, b in (('Helpers', 'Agents'), ('helpers', 'agents'), ('Helper', 'Agent'), ('helper', 'agent')):
        s = re.sub(rf'\b{a}\b', b, s)
    return s


JOB = {'clover': 'nurse agent', 'mochi': 'support agent', 'luna': 'UI designer', 'taro': 'maintenance tech', 'pip': 'café assistant', 'remy': 'coding buddy',
       'nova': 'tutor', 'otto': 'lab technician'}   # reports call the test agents by job, not by their test names
NAME_RE = re.compile(r'\b(' + '|'.join(n.capitalize() for n in JOB) + r')\b')


def clean(text):   # replies as published: no local paths
    text = re.sub(r'[A-Za-z]:[\\/][^\s`"\')]*[\\/]hce[\\/]team', 'my-team', text)
    return re.sub(r'[A-Za-z]:[\\/][^\s`"\')]+', '…', text)


def write_md(results, c, ver, model, date):
    a, p = c['active'], c['passive']
    names = {'review': 'Reply to a one-star review', 'medical': 'Explain a medical word', 'website': 'One-page café website (two-part)',
             'bug': 'Fix a Python KeyError', 'machine': 'Espresso machine error', 'design': 'Is this text contrast OK?',
             'homework': "A child's fractions homework", 'lab': 'Make a 1:50 dilution', 'bakesale': 'Bake-sale menu and sign-up page (two-part)',
             'none': 'Kyoto trip (no helper fits)'}
    jobs = lambda keys: ', '.join(JOB[k] for k in keys) or 'none'
    rows = '\n'.join(f"| {names[t]} | {a['tasks'][t][0]} of {a['tasks'][t][1]} | {jobs(a['tasks'][t][2])} | "
                     f"{p['tasks'][t][0]} of {p['tasks'][t][1]} | {jobs(p['tasks'][t][2])} |" for t in names)
    def example(task, mode):
        r = next((r for r in results if r.get('part') == 1 and r.get('task') == task and r.get('mode') == mode and not r.get('error')), None)
        if not r:
            return '(no finished run)'
        body = NAME_RE.sub('[name]', clean(r['reply']).strip())
        body = body if len(body) < 900 else body[:900].rsplit(' ', 1)[0] + ' …'
        return '\n'.join('> ' + line if line else '>' for line in body.splitlines())
    md = f'''# First test: with and without a Helpercraft team folder

Tested on {date} with Claude Code {ver} ({model}), in a clean setup with no personal settings, plugins or add-ons.
The plan and scoring rules were written and committed before the full run: [tests/team_eval.md](../tests/team_eval.md). Three sentences in it were corrected after the run, and the plan quotes the originals.
Our second, bigger test, which also scores the answers against the AI alone, is in [evaluation.md](evaluation.md).

@@WORDS@@

<picture><source media="(prefers-color-scheme: dark)" srcset="readme/eval-dark.png"><img src="readme/eval-light.png" width="600" alt="With the team folder against without it (the same helpers as installed skills). Picked the right helper: {a['right']} of {a['runs1']} against {p['right']} of {p['runs1']}. Asked before starting, by design: {a['asked']} of {a['runs1']} against {p['asked']} of {p['runs1']}. Still knew its helper after the conversation was squeezed: {a['kept']} of {a['runs2']} against {p['kept']} of {p['runs2']}. Helper's rules put back in view right after the squeeze: {a['came_back']} of {a['runs2']} against {p['came_back']} of {p['runs2']}. Back to the helper after one step: {a['back']} of {a['runs2']} against {p['back']} of {p['runs2']}."></picture>

## What we found

- **Both picked the right helper most of the time.** The team folder did in {a['right']} of {a['runs1']} runs and installed skills in {p['right']} of {p['runs1']}. At this size, that difference alone means little.
- **For a bigger job, the team folder built a team.** For the two two-part tasks it proposed {a['multi']:.1f} helpers on average; installed skills used {p['multi']:.1f}. For the café website, installed skills used a helper in {p['tasks']['website'][0]} of {p['tasks']['website'][1]} runs, and the AI did the whole job itself.
- **With the team folder, you decide first.** It asked before starting in {a['asked']} of {a['runs1']} runs. With installed skills, the first reply already did the task in {p['did_task']} of {p['runs1']}. The {p['asked']} times it asked, it was about the task, such as which machine model, not about which helper to use.
- **It reads, it doesn't copy.** With the team folder, the AI read `START-HERE.md` in {a['start']} of {a['runs1']} runs, opened no helper's file before the OK ({a['first']} of {a['runs1']}), and afterwards read the chosen helper's file where it is ({a['in_place']} of {a['runs2']}).
- **After the conversation was squeezed, both still knew their helper, but not in the same way.** Both passed the check: {a['kept']} of {a['runs2']} (team folder) and {p['kept']} of {p['runs2']} (installed skills). With the team folder, the AI had opened the helper's file, and Claude Code put that file back in view right after the squeeze ({a['came_back']} of {a['runs2']}); the AI answered without looking anything up ({a['from_memory']} of {a['runs2']}). An installed skill's rules came back in {p['came_back']} of {p['runs2']}, and the AI dug through its saved copy of the old conversation before answering ({p['looked_back']} of {p['runs2']}). Keeping that copy and putting opened files back are Claude Code features; other tools may not do either. (We found this in the logs while checking the results. It wasn't one of the pre-set scores.)

## What was compared

The same 8 helpers (made with Helpercraft: a nurse agent, a support agent, a UI designer, a maintenance tech, a café assistant, a coding buddy, a tutor and a lab technician), used two ways:

- **Team folder (active):** the AI gets Helpercraft's "Copy for my AI" sentence and a task. `START-HERE.md` asks it to suggest who fits and wait for an OK.
- **Installed skills (passive):** the same `SKILL.md` files in Claude Code's own skills folder. The AI gets only the task and decides by itself whether to use one.

10 tasks, each run 3 times per way. Then 3 tasks where the conversation was squeezed (`/compact`, what AI tools do in long sessions) to see whether the AI still knew its helper, and whether one step brought the helper back: pasting the sentence again (team folder) or typing the skill's command (installed skills).

A pick counts as right when it includes at least one helper that fits the task and none that don't; for the Kyoto trip, right means no helper at all. Under a stricter rule, every helper that fits, the team folder scores {a['strict']} of {a['runs1']} and installed skills {p['strict']} of {p['runs1']}.

## Results

| | Team folder | Installed skills |
|---|---|---|
| Picked the right helper | **{a['right']} of {a['runs1']}** | **{p['right']} of {p['runs1']}** |
| Asked before starting (by design, not a score) | {a['asked']} of {a['runs1']} | {p['asked']} of {p['runs1']} |
| Helpers proposed for the two-part tasks (average) | {a['multi']:.1f} | {p['multi']:.1f} |
| Still knew its helper after the squeeze | {a['kept']} of {a['runs2']} | {p['kept']} of {p['runs2']} |
| … by re-reading the helper's file | {a['reread']} of {a['runs2']} | {p['reread']} of {p['runs2']} |
| … with the helper's rules put back in view (found in the logs) | {a['came_back']} of {a['runs2']} | {p['came_back']} of {p['runs2']} |
| … after digging through the old conversation (found in the logs) | {a['looked_back']} of {a['runs2']} | {p['looked_back']} of {p['runs2']} |
| Back to the helper after one step | {a['back']} of {a['runs2']} | {p['back']} of {p['runs2']} |

With the team folder, the AI read `START-HERE.md` in {a['start']} of {a['runs1']} runs and opened a helper's own file before the OK in {a['first']}. After the OK it read the chosen helper's file where it is, without copying it, in {a['in_place']} of {a['runs2']}.
Runs that timed out or failed are left out of the counts: {a['errors1'] + a['errors2']} (team folder), {p['errors1'] + p['errors2']} (installed skills).

### Task by task

| Task | Team folder: right | Suggested | Installed skills: right | Used |
|---|---|---|---|---|
{rows}

### What the replies looked like (café website task)

Team folder:

@@EXAMPLE_ACTIVE@@

Installed skills:

@@EXAMPLE_PASSIVE@@

## Limits

- One tool so far: Claude Code. More AI agents and models are planned.
- AI replies vary from run to run, so each case ran 3 times. Small differences between the two ways aren't meaningful at this size.
- The squeeze was a manual `/compact` after a short conversation, not a naturally long session.
- A separate, smaller model (Claude Haiku) judged which helpers each reply proposed. It saw only the reply, never which way produced it.
- In the team-folder runs, the user's OK names the helper ("OK, go with [name].") before the squeeze. Installed-skill runs have no such message, because the AI picks by itself. That's how each way works, but it may explain part of the difference after the squeeze.
- Both ways could only read files (Read, Glob, Grep, Skill), so "did the task" means the AI wrote the answer in the chat.

## Run it yourself

With the Claude Code CLI signed in: `python tests/team_eval.py` (about 20 minutes; it uses your plan). `--pilot` runs a small version first.
'''
    words = ('**About the words:** when this test ran, Helpercraft called its agents "helpers" and gave each one a name. The prompts, the files and the '
             'AI\'s replies quoted below use those words. On 30 September 2026 the app renamed them "agents" and made names optional. This report uses the '
             'new words, calls each test agent by its job, and shows names in quotes as [name].')
    md = agents(md).replace('@@WORDS@@', words).replace('@@EXAMPLE_ACTIVE@@', example('website', 'active')).replace('@@EXAMPLE_PASSIVE@@', example('website', 'passive'))
    (ROOT / 'docs' / 'evaluation-1.md').write_text(md, encoding='utf-8', newline='\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pilot', action='store_true')
    ap.add_argument('--runs', type=int, default=3)
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--report', metavar='RESULTS_JSON', help='draw the chart and print the counts from a finished run')
    a = ap.parse_args()
    if a.report:
        report(a.report); return
    tasks = ['review', 'website'] if a.pilot else [t[0] for t in TASKS]
    squeeze = SQUEEZE[:1] if a.pilot else SQUEEZE
    runs = 1 if a.pilot else a.runs
    setup()
    jobs = [(part1, (t, m, r)) for r in range(runs) for t in tasks for m in ('active', 'passive')]
    jobs += [(part2, (t, k, h, m, r)) for r in range(runs) for t, k, h in squeeze for m in ('active', 'passive')]
    print(f'{len(jobs)} cases, {a.workers} at a time', flush=True)
    results = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(f, *args): args for f, args in jobs}
        for fut in cf.as_completed(futs):
            try:
                res = fut.result()
            except Exception as e:   # a crash in one case is recorded, not fatal
                res = {'error': f'crash: {e}', 'args': list(map(str, futs[fut]))}
            results.append(res)
            print(len(results), '/', len(jobs), res.get('part'), res.get('task'), res.get('mode'),
                  'error' if res.get('error') else ('correct' if res.get('correct') else '') + (' kept' if res.get('kept_after_squeeze') else ''), flush=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M')
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f'results-{"pilot-" if a.pilot else ""}{stamp}.json'
    path.write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
    print('saved', path)


if __name__ == '__main__':
    main()
