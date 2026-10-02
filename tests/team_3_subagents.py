"""Evaluation 3's setup D: the 18 team agents as Claude Code subagents, written by the app itself. Each agent from the
team's backup is loaded into the studio, as Agent home's "Open in the studio" does, and its "Download as a subagent" text
(buildSkill().agent) is saved. Each agent's skill text must match tests/fixtures/team-3 exactly, which proves the right
agent was loaded. Output: tests/fixtures/team-3-subagents/<name>.md
    python tests/team_3_subagents.py"""
import ast, json, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
TEAM = ROOT / 'tests' / 'fixtures' / 'team-3'
OUT = ROOT / 'tests' / 'fixtures' / 'team-3-subagents'
# the same 18 agents and looks as tests/team_3.py (read from its source, so the two can't drift)
src = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse((ROOT / 'tests' / 'team_3.py').read_text(encoding='utf-8')).body
       if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ('TEAM', 'KINDS')}
backup = json.dumps({'app': 'helpercraft', 'version': 2, 'agents': [
    {'slot': i, 'id': f'e3{i:04d}team', 'thumb': None, 'state': {'name': '', 'role': r, 'specialty': sp, 'hatched': True, 'look': src['KINDS'][i % len(src['KINDS'])]}}
    for i, (r, sp) in enumerate(src['TEAM'])]}).encode()
html = (ROOT / 'helpercraft.html').read_text(encoding='utf-8')
with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome')
    ctx = b.new_context()
    ctx.route('http://helpercraft.test/**', lambda route: route.fulfill(body=html, content_type='text/html; charset=utf-8'))
    p = ctx.new_page()
    p.on('dialog', lambda d: d.accept())
    p.goto('http://helpercraft.test/helpercraft.html?nogl')
    p.wait_for_function('() => window.Helpercraft')
    p.set_input_files('#restoreFile', files=[{'name': 'backup.json', 'mimeType': 'application/json', 'buffer': backup}])
    p.wait_for_function("() => /Restored/.test(document.querySelector('#toast').textContent)", timeout=60000)
    if p.evaluate("() => document.querySelector('#homeDlg').open"):
        p.keyboard.press('Escape')
    made = []
    for i, (_, specialty) in enumerate(src['TEAM']):
        # Agent home: the agent's room (9 spots each), its card, then "Open in the studio"
        p.click('#homeBtn')
        while p.is_enabled('#roomPrev'):
            p.click('#roomPrev')
        for _ in range(i // 9):
            p.click('#roomNext')
        p.locator('#homeDlg').get_by_text(specialty, exact=True).first.click()
        p.locator('#homeDlg').get_by_role('button', name='Open in the studio').click()
        p.wait_for_function('(sp) => window.Helpercraft.state.specialty === sp', arg=specialty)
        made.append(p.evaluate('() => { const s = window.Helpercraft.buildSkill(); return { slug: s.slug, text: s.text, agent: s.agent }; }'))
    b.close()

def split(text):   # (name and description lines, body) of a skill or subagent file
    head, body = text.split('\n---\n', 1)
    return [l for l in head.splitlines() if l.startswith(('name: ', 'description: '))], body
shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
for m in made:
    skill = (TEAM / 'agents' / m['slug'] / 'SKILL.md').read_text(encoding='utf-8')
    assert split(m['text']) == split(skill), f"{m['slug']}: the studio's skill text differs from the team folder's"
    assert split(m['agent']) == split(skill), f"{m['slug']}: the subagent's name, description or body differs"
    (OUT / f"{m['slug']}.md").write_text(m['agent'], encoding='utf-8', newline='\n')
names = sorted(f.stem for f in OUT.iterdir())
assert names == sorted(d.name for d in (TEAM / 'agents').iterdir() if d.is_dir()), names
print(len(names), 'subagents, each matching its team skill:', ', '.join(names))
