#!/usr/bin/env python3
"""Evaluation 4: fresh tasks, and a user who answers questions. The plan and its scoring rule: tests/team_eval_4.md.

The same setups, tools, limits, judge and rules as Evaluation 3 (tests/team_eval_3.py, reused), with these changes:
  - the 90 tasks of tests/fixtures/tasks-4.json, in six groups of 15 by number of steps, and the team folder made by 1.0.4
  - a pretend user who answers what it's asked from the task's hidden details (its prompt and model below, every reply logged)
  - up to 5 user messages; the judge also sees the hidden details and the checks
  - a reader for how many hidden details reached each answer, and the steps result (4-6+ steps against 1-3)
  - after the pilots (tests/team_eval_4.md): no automatic result for a missing page, any format that does the job is fine,
    and the pretend user's replies are written by the code from the hidden details (a small model only sorts what the AI
    asks); it ends the chat when it has nothing new to say

    python tests/team_eval_4.py run --pilot          # 6 tasks (the first of each group) x 4 setups, not counted
    python tests/team_eval_4.py run [--resume FILE]  # all 90 x 4
    python tests/team_eval_4.py check FILE           # pages, checks, safety rules, first replies, details used
    python tests/team_eval_4.py judge FILE           # the Sonnet judge, both orders
    python tests/team_eval_4.py score FILE
    python tests/team_eval_4.py run --team team-4b --reuse tests/results/team-eval-4/run-claude-20261003-1555.json --setups C
                                                     # (superseded: the check runs all of it on one day, below)
    python tests/team_eval_4.py run --team team-3b --setups AC   # the check of the fix, same day: A and the old team folder,
    python tests/team_eval_4.py run --team team-4b --setups C    # then the new team folder (resume each with the same options),
    python tests/team_eval_4.py check-merge MAIN BEFORE AFTER    # then one file with Evaluation 4's B and D; check, judge, score it"""
import argparse, json, random, re, sys, importlib.util
from pathlib import Path
import concurrent.futures as cf
ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('team_eval_3', ROOT / 'tests' / 'team_eval_3.py')
te = importlib.util.module_from_spec(spec); spec.loader.exec_module(te)

TASKS = json.loads((ROOT / 'tests' / 'fixtures' / 'tasks-4.json').read_text(encoding='utf-8'))
for t in TASKS:   # test 3's page logic keys on "long-page"; here a task needs a page when its writer said so
    t['category'] = 'long-page' if t['page'] else f"steps-{t['steps_group']}"
te.TASKS, te.TASK = TASKS, {t['id']: t for t in TASKS}
te.RULES = {t['id']: (t['rule'], t['breaking']) for t in TASKS if 'safety' in t['flags']}
te.PILOT = [next(t['id'] for t in TASKS if t['steps_group'] == g) for g in range(1, 7)]   # the first task of each group
te.OWNER_TASKS = set(te.PILOT)   # the harness was tuned on the pilot tasks, so each verdict is also given without them
te.TEAM = ROOT / 'tests' / 'fixtures' / 'team-3b'
te.OUT = ROOT / 'tests' / 'results' / 'team-eval-4'
te.MAX_TURNS = 5
te.PLAN = 'tests/team_eval_4.md'
te.AUTO_PAGE_LOSS = False   # the owner's decision after the pilots: the judge decides every page task
te.LEAK_MARKS = te.LEAK_MARKS + ('tasks-4.json', 'team_eval_4', 'team-3b', 'team-4b')
te.CHECK_PLAN = 'tests/team_eval_4_check.md'   # the check of the fix after Evaluation 4
# The check's reused B and D answers were written on 3 October, its new ones on 8 October. A task is date-related when its text,
# hidden details or checks name a date from 3 to 31 October or say this/next week, weekend or month, tomorrow, tonight or today
# (the rule fixed in tests/team_eval_4_check.md before the check ran); the check also gives each verdict without them.
_DAY = r'(?:[3-9]|[12]\d|3[01])'
DATE_RULE = re.compile(rf'\b{_DAY}(?:st|nd|rd|th)?\s+(?:of\s+)?Oct(?:ober)?\b|\bOct(?:ober)?\.?\s+{_DAY}(?:st|nd|rd|th)?\b'
                       r'|\b(?:this|next)\s+(?:week|weekend|month)\b|\btomorrow\b|\btonight\b|\btoday\b', re.I)
DATE_TASKS = {t['id'] for t in TASKS if DATE_RULE.search(' '.join([t['task'], *t['hidden_details'], *t['checks']]))}
USER_MODEL = te.MODEL   # Sonnet sorts the AI's questions: in a replay of pilot 3, Haiku failed on 5 of 58 long messages
te.READER_MODEL = te.MODEL   # the waiting reader too: every AI role in Evaluation 4 is Sonnet (the owner's "Sonnet only")
FORMAT = 'Any format that does the job is fine (for example a spreadsheet instead of a web page), unless the person asked for a specific one.'
te.CHECKS = te.CHECKS.replace('For each check say', f'A check that names a format passes if the work does the same job another way. {FORMAT}\nFor each check say')

# The pretend user (after pilot 3): a small model only sorts what the AI asks; the code writes the reply from the task's
# hidden details, word for word, and fixed phrases, so the reply can't hold a made-up fact.
USER = '''You read a message from an AI assistant to a person who asked it for help, and sort out what it asks the person. Answer with JSON only, no other text.

The person's request:
<<<
{task}
>>>

What the person knows but didn't type (numbered):
{details}

The assistant's message:
<<<
{text}
>>>

List each thing the message asks the person, wherever it appears, including inside an option (such as "or tell me your prices first"). Inside an option the person won't pick, list only what one of the details answers. Check every numbered detail against each thing asked. For each, give:
- "asked": what it asks about, in a few words (for example "the shop hours")
- "type": one of
  - "detail": information about the person or their situation (a fact, number, name, date or preference, or whether something about them is right), even when the message suggests example answers such as "cash or bank transfer?"
  - "ok": an OK to start or carry on, a question about which part of the work to do next, or an offer to do more of what the person asked for or needs (going by the request and the details above)
  - "choice": picking one of the lettered or numbered options it lists for how to go about the work, such as a plan or a setup
  - "extra": an offer of something clearly outside the request that the details don't call for, such as saving a new agent for next time, or a copy in another file format
  - "open": an open question such as "anything else I should know?"
- "details": for "detail", the numbers of the details above that directly answer it ([] if none do). If a detail answers something of another type, such as an offer of a version the person needs, make it a "detail" with that number.
- "pick": for "choice", the letter or number of the option to pick: the one it recommends; if it recommends none, the one where the person gives their details first, if there is one; otherwise the first
Return {{"items": [{{"asked": "...", "type": "...", "details": [], "pick": ""}}]}}.'''
GO = 'Yes, please go ahead, and do all the rest of what I asked for now.'
RECOMMENDED = 'Go ahead with your recommendation.'
NO = 'No thanks to the extras you offered.'

# Pilot fix (2 October 2026): the chat went on only while nothing was handed over, so "send me your prices and I'll finish
# it" ended it. Now it goes on while requested work is unfinished and the AI asks for what it needs to finish it; has_work
# keeps handed-over work in the judged answer.
WAITING = '''You read one message from an AI assistant to a user. Answer with JSON only, no other text.

The user's request:
<<<
{task}
>>>

Files the assistant has written so far: {files}

The assistant's message:
<<<
{text}
>>>

1. unfinished: is some of the requested work not done yet? true if the assistant hasn't started, has left parts of the request for later, or has left blanks, placeholders or made-up stand-in details that it offers to replace with the user's real ones.
2. waiting: true only if unfinished is true and the message asks the user for what it needs to do or finish that work (details, a choice, or an OK to start or carry on). false if it treats the requested work as finished and only asks whether the user wants changes, asks the user to check something themselves, or offers extras nobody asked for (such as a file, a PDF, a translation, another version, or a new agent or helper); false if it asks nothing, or says it can't help.
3. has_work: does the message itself contain some of what the user asked for, such as a draft, a message, a schedule, a budget, a list or a page? A plan for the user's own situation (such as their week-by-week to-do list) counts; a description of what the assistant will make or do, options, and questions don't.
Return {{"unfinished": true or false, "waiting": true or false, "has_work": true or false}}.'''
te.WAITING = WAITING

DETAILS = '''You read an AI assistant's finished work for a person. Answer with JSON only, no other text.

The person's request:
<<<
{task}
>>>

Details the person knew (numbered):
{details}

The work (its messages, then each file it wrote):
<<<
{answer}
>>>

Which numbered details does the work actually use or reflect correctly? A detail counts if the work fits it, even in other words. It doesn't count if the work assumes something different, or leaves it as a blank to fill in.
Return {{"used": [the numbers]}}.'''


def numbered(details):
    return '\n'.join(f'{i + 1}. {d}' for i, d in enumerate(details))


def compose(details, items, turns):
    """The reply from sorted items, in this order: the picked option, matching details word for word, "use your best
    judgement" for anything they don't cover, an OK to finish everything, no thanks to extras. A pick that isn't a short
    option label becomes "go ahead with your recommendation", so no preference is made up. A reply with no pick and no
    detail the person hasn't given before has nothing new; the second such reply ends the chat instead. Returns (reply, or
    None when the chat ends; the details given; whether it had nothing new)."""
    picks, said, given, unknown, ok, extra = [], [], [], [], False, False
    for it in items:
        if not isinstance(it, dict):
            continue
        kind, asked = it.get('type'), str(it.get('asked') or '').strip().rstrip('?.')
        nums = [n for n in it.get('details') or [] if isinstance(n, int) and 1 <= n <= len(details)]
        if nums:   # a detail answers it, whatever its type
            for n in nums:
                if n not in given:
                    said.append(details[n - 1].rstrip('.') + '.'); given.append(n)
        elif kind == 'detail':
            unknown.append(asked or 'the rest')
        elif kind == 'choice':
            pick = str(it.get('pick') or '').strip().rstrip('.)').lstrip('(')
            picks.append(f'Option {pick}.' if 0 < len(pick) <= 3 else RECOMMENDED)
        elif kind == 'ok':
            ok = True
        elif kind == 'extra':
            extra = True
    unknown = list(dict.fromkeys(unknown))
    best = [f"Use your best judgement on {'; '.join(unknown[:3])}{'; and the rest' if len(unknown) > 3 else ''}."] if unknown else []
    parts = list(dict.fromkeys(picks)) + said + best + ([GO] if ok else [])
    before = {n for x in turns[:-1] for n in (x.get('user') or {}).get('details_given', [])}
    nothing_new = not picks and all(n in before for n in given)
    if not parts or (nothing_new and any((x.get('user') or {}).get('nothing_new') for x in turns[:-1])):
        return None, [], nothing_new   # nothing to say, or nothing new for the second time: the person ends the chat
    return ' '.join(parts + ([NO] if extra else [])), given, nothing_new


def user_reply(tid, turns):
    """The pretend user: answers what the AI asks from the hidden details, or ends the chat (None) when it has nothing new to
    say. The sorted items, the reply and the details in it are logged on the AI's turn; if the sorting can't be read, it says OK."""
    t = te.TASK[tid]
    v, cost = te.ask(USER.format(task=t['task'], details=numbered(t['hidden_details']), text=turns[-1]['text']), model=USER_MODEL)
    items = v.get('items') if isinstance(v, dict) else None
    if not isinstance(items, list):
        turns[-1]['user'] = {'reply': te.OK, 'end': False, 'details_given': [], 'items': None, 'nothing_new': False, 'fallback': True, 'cost': cost}
        return te.OK
    reply, given, nothing_new = compose(t['hidden_details'], items, turns)
    turns[-1]['user'] = {'reply': reply, 'end': reply is None, 'details_given': given, 'items': items, 'nothing_new': nothing_new,
                         'fallback': False, 'cost': cost}
    return reply


te.user_reply = user_reply


def question_only(t):
    has_work = (t.get('reader') or {}).get('has_work')
    return t.get('waiting') and not t['files'] and has_work is not True


def answer(rec, replies=False):
    """As in Evaluation 3, except that a question turn which also hands over some of the work stays in (the reader's has_work).
    With replies (the judge's text), the person's reply to each kept message follows it, so a draft and its later version make
    sense; replies to pure questions stay out with the questions."""
    parts = []
    for t in rec['turns']:
        if t.get('text', '').strip() and not question_only(t):
            parts.append(t['text'].strip())
            if replies and (t.get('user') or {}).get('reply'):
                parts.append(f"[The person replied: {t['user']['reply']}]")
    if not parts and rec['turns']:
        parts = [rec['turns'][-1].get('text', '').strip()]
    out = '\n\n---\n\n'.join(parts)
    for f in rec['files']:
        out += f"\n\n[File: {f['path']}]\n{f['content']}"
    return out


te.answer = answer
te.judged = lambda rec: answer(rec, replies=True)


def pair_extra(t, c, o, c_first):
    """The judge sees the hidden details, the checks, that any format is fine, how to read drafts (and, for a page task, the
    browser check)."""
    extra = ('\nWhat the person knows but didn\'t type (they would have said it if asked):\n' + '\n'.join(f'- {d}' for d in t['hidden_details']) +
             '\nAn answer that fits these details, by asking or by sensible stated assumptions, serves the person better.\n'
             '\nWhat the finished work must do (written with the request, before any answer existed):\n' + '\n'.join(f'- {x}' for x in t['checks']) +
             f'\n{FORMAT}\nAn answer may hold drafts, with the person\'s replies in [brackets]; judge the final version of the work.\n')
    if t['page']:
        p1, p2 = (c, o) if c_first else (o, c)
        note = lambda r: te.describe_pages(r.get('pages')).replace('no page delivered', 'no web page made')
        extra += f"\nIf an answer made a web page, a browser opened it offline. Answer 1: {note(p1)}. Answer 2: {note(p2)}.\n"
    return extra


te.pair_extra = pair_extra


def do_details(data, path, workers=4):
    runs = [r for r in te.ok_runs(data).values() if not r.get('error') and 'details_used' not in r]
    def one(r):
        t = te.TASK[r['task']]
        v, cost = te.ask(DETAILS.format(task=t['task'], details=numbered(t['hidden_details']), answer=te.answer(r)))
        r['details_used'] = sorted({n for n in ((v or {}).get('used') or []) if isinstance(n, int) and 1 <= n <= len(t['hidden_details'])}) if isinstance(v, dict) else None
        r['check_cost'] = r.get('check_cost', 0) + cost
    with cf.ThreadPoolExecutor(workers) as ex:
        for _ in ex.map(one, runs):
            te.save(data, path)


def diff_range(short, long, n=10000, seed=2026):
    """The steps result: rate(4-6+) minus rate(1-3), with a 95% range from resampling the tasks in each part."""
    val = lambda o: 1.0 if o == 'C' else 0.5 if o == 'tie' else 0.0
    a, b = [val(o) for o in short if o in ('C', 'other', 'tie')], [val(o) for o in long if o in ('C', 'other', 'tie')]
    if not a or not b:
        return None
    rnd = random.Random(seed)
    d = sorted(sum(rnd.choice(b) for _ in b) / len(b) - sum(rnd.choice(a) for _ in a) / len(a) for _ in range(n))
    return {'difference': round(sum(b) / len(b) - sum(a) / len(a), 3), 'low': round(d[int(0.025 * n)], 3), 'high': round(d[int(0.975 * n) - 1], 3),
            'helps more on longer tasks': d[int(0.025 * n)] > 0}


def score(data):
    s = te.score(data)
    s['comparisons'] = {k: {('without the 6 pilot tasks' if sub == 'without my tasks' else sub): v for sub, v in comp.items()} for k, comp in s['comparisons'].items()}
    if data.get('note') == te.CHECK_PLAN:   # the check of the fix: each verdict also without the date-related tasks
        for k, comp in s['comparisons'].items():
            by_judge = {}
            for judge, rows in (data.get('judged') or {}).items():
                rows = [x for x in rows if x['vs'] == k.split(' vs ')[1] and x['task'] not in DATE_TASKS]
                by_judge[judge] = te.rate([x['outcome'] for x in rows]) | {'judging errors': sum(x['outcome'] == 'error' for x in rows)}
            comp[f'without the {len(DATE_TASKS)} date-related tasks'] = {'judges': by_judge, 'verdict': te.verdict_word(by_judge)}
    best = te.ok_runs(data)
    group = {t['id']: t['steps_group'] for t in TASKS}
    s['steps'] = {}
    for judge, rows in (data.get('judged') or {}).items():
        for other in te.others(data):
            mine = [x for x in rows if x['vs'] == other]
            s['steps'][f'C vs {other} ({judge})'] = {
                'by group': {g: te.rate([x['outcome'] for x in mine if group[x['task']] == g]) for g in range(1, 7)},
                '4-6+ minus 1-3': diff_range([x['outcome'] for x in mine if group[x['task']] <= 3], [x['outcome'] for x in mine if group[x['task']] >= 4])}
    for setup, b in s['behaviour'].items():
        rs = [r for (t, su), r in best.items() if su == setup and not r.get('error') and not r.get('leaked')]
        given = [len({n for turn in r['turns'] for n in (turn.get('user') or {}).get('details_given', [])}) for r in rs]
        used = [len(r['details_used']) for r in rs if r.get('details_used') is not None]
        total = sum(len(te.TASK[r['task']]['hidden_details']) for r in rs)
        b['hidden details the user gave'] = f'{sum(given)} of {total}'
        b['hidden details used in the answer'] = f'{sum(used)} of {total}'
        b['pretend-user fallbacks'] = sum(bool((turn.get('user') or {}).get('fallback')) for r in rs for turn in r['turns'])
        b['chats the pretend user ended'] = sum(bool((r['turns'][-1].get('user') or {}).get('end')) for r in rs if r['turns'])
    return s


def merge_check(main_path, before_path, after_path):
    """The check of the fix (tests/team_eval_4_check.md): A and the old team folder (as O) from today's run with team-3b, the
    new team folder (C) from today's run with team-4b, and B and D reused from Evaluation 4's main run. -> check-claude-*.json"""
    main, before, after = (json.loads(Path(x).read_text(encoding='utf-8')) for x in (main_path, before_path, after_path))
    assert (before['team'], after['team']) == ('team-3b', 'team-4b') and before['version'] == after['version'] == main['version'], 'teams or versions'
    last = lambda d, su: [r for r in te.ok_runs(d).values() if r['setup'] == su]
    data = {k: after[k] for k in ('plan', 'tool', 'model', 'effort', 'tools', 'max_turns', 'version')}
    data.update(pilot=False, note=te.CHECK_PLAN, team='team-4b', started=before['started'], finished=after.get('finished'),
                made_from={'A and O (team-3b)': Path(before_path).name, 'C (team-4b)': Path(after_path).name, 'B and D': Path(main_path).name},
                runs=last(before, 'A') + [{**r, 'setup': 'O'} for r in last(before, 'C')] + last(after, 'C') + last(main, 'B') + last(main, 'D'))
    out = te.OUT / f"check-claude-{after['started'][:10].replace('-', '')}.json"
    te.save(data, out)
    print(len(data['runs']), 'runs ->', out)
    return out


def _check():
    assert len(TASKS) == 90 and all(sum(t['steps_group'] == g for t in TASKS) == 15 for g in range(1, 7))
    flags = [f for t in TASKS for f in t['flags']]
    assert (flags.count('no-fit'), flags.count('safety'), flags.count('low-help')) == (8, 8, 6), flags
    assert len(te.RULES) == 8 and len(te.PILOT) == 6 and te.MAX_TURNS == 5
    assert all(3 <= len(t['hidden_details']) <= 6 and 2 <= len(t['checks']) <= 5 for t in TASKS)
    assert sorted(d.name for d in (te.TEAM / 'agents').iterdir() if d.is_dir()) == te.AGENTS
    assert diff_range(['other'] * 20, ['C'] * 20)['helps more on longer tasks'] and not diff_range(['C', 'other'] * 10, ['other', 'C'] * 10)['helps more on longer tasks']
    plan = {'text': 'Plan: A or B?', 'waiting': True, 'files': [], 'reader': {'waiting': True, 'has_work': False}}
    part = {'text': 'Draft: hi. Your name?', 'waiting': True, 'files': [], 'reader': {'waiting': True, 'has_work': True}}
    done = {'text': 'Done.', 'waiting': False, 'files': []}
    assert answer({'turns': [plan, part, done], 'files': []}) == 'Draft: hi. Your name?\n\n---\n\nDone.'
    assert answer({'turns': [dict(part, reader=None), done], 'files': []}) == 'Done.'   # runs without has_work: the old rule
    rec = {'turns': [dict(plan, user={'reply': 'A'}), dict(part, user={'reply': 'Rui'}), done], 'files': []}
    assert te.judged(rec) == 'Draft: hi. Your name?\n\n---\n\n[The person replied: Rui]\n\n---\n\nDone.'   # no reply to the plan
    assert te.AUTO_PAGE_LOSS is False and 'Any format' in te.CHECKS
    assert len(DATE_TASKS) == 32 and {'t07', 't13', 't61', 't81'} <= DATE_TASKS and 't01' not in DATE_TASKS   # as listed in tests/team_eval_4_check.md
    ask = te.ask
    try:   # the pretend user, with a stubbed reader
        d = te.TASK['t01']['hidden_details']
        turns = [{'text': 'Which option, and your name? And the date?'}]
        te.ask = lambda *a, **k: ({'items': [{'type': 'choice', 'pick': 'B'}, {'type': 'detail', 'details': [1, 99], 'asked': 'name'},
                                             {'type': 'detail', 'details': [], 'asked': 'the till'}, {'type': 'open'}]}, 0)
        r = user_reply('t01', turns)
        assert r == f"Option B. {d[0].rstrip('.')}. Use your best judgement on the till." and turns[-1]['user']['details_given'] == [1]
        te.ask = lambda *a, **k: ({'items': [{'type': 'extra', 'asked': 'a PDF'}, {'type': 'detail', 'details': [], 'asked': 'the till'}]}, 0)
        turns = [{'text': 'x'}]
        assert user_reply('t01', turns) == f'Use your best judgement on the till. {NO}' and turns[-1]['user']['nothing_new']
        turns.append({'text': 'and the till?'})
        assert user_reply('t01', turns) is None and turns[-1]['user']['end']   # best judgement again: the chat ends
        te.ask = lambda *a, **k: ({'items': [{'type': 'detail', 'details': [1]}, {'type': 'ok'}]}, 0)
        turns = [{'text': 'name?'}]
        assert user_reply('t01', turns) and not turns[-1]['user']['nothing_new']   # a new detail
        turns.append({'text': 'name again?'})
        assert user_reply('t01', turns) and turns[-1]['user']['nothing_new']   # the same detail and "go ahead": nothing new, once
        turns.append({'text': 'name once more?'})
        assert user_reply('t01', turns) is None   # nothing new twice: the chat ends
        te.ask = lambda *a, **k: ({'items': [{'type': 'extra'}, {'type': 'open'}]}, 0)
        assert user_reply('t01', [{'text': 'PDF too?'}]) is None   # only extras and open questions: the chat ends
        te.ask = lambda *a, **k: ({'items': [{'type': 'ok'}]}, 0)
        assert user_reply('t01', [{'text': 'Shall I do step 4?'}]) == GO
        te.ask = lambda *a, **k: ({'items': [{'type': 'choice', 'pick': 'cash'}, {'type': 'ok', 'details': [3]}]}, 0)   # no made-up pick
        assert user_reply('t01', [{'text': 'Cash or transfer? A Portuguese version?'}]) == f"{RECOMMENDED} {d[2].rstrip('.')}." 
        te.ask = lambda *a, **k: (None, 0)
        turns = [{'text': 'x'}]
        assert user_reply('t01', turns) == te.OK and turns[-1]['user']['fallback']
    finally:
        te.ask = ask


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run'); r.add_argument('--pilot', action='store_true'); r.add_argument('--tasks'); r.add_argument('--setups', default='ABCD')
    r.add_argument('--workers', type=int, default=4); r.add_argument('--resume')
    r.add_argument('--team', default='team-3b'); r.add_argument('--reuse')   # the check of the fix: --team team-4b --reuse <main run> --setups C
    for name in ('check', 'judge', 'score'):
        s = sub.add_parser(name); s.add_argument('file')
    m = sub.add_parser('check-merge'); m.add_argument('main'); m.add_argument('before'); m.add_argument('after')
    a = ap.parse_args()
    if a.cmd == 'run':
        return te.do_run(a)
    if a.cmd == 'check-merge':
        return merge_check(a.main, a.before, a.after)
    path = Path(a.file); data = json.loads(path.read_text(encoding='utf-8'))
    if a.cmd == 'check':
        te.do_checks(data, path); do_details(data, path)
    elif a.cmd == 'judge':
        te.do_judge(data, path)
    data['scores'] = score(data); te.save(data, path)
    print(json.dumps(data['scores'], ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    _check()
    main()
