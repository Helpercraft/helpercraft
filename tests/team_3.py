"""Evaluation 3's team, made the way people make it: 18 agents with no names (they go by their jobs), restored into the
app, then Agent home's own "Download the team (.zip)", unzipped to tests/fixtures/team-3. Look-alike pairs test picking.
Run once, before the experiment; the team is then frozen with the plan (tests/team_eval_3.md).
    python tests/team_3.py"""
import io, json, shutil, sys, zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'tests' / 'fixtures' / 'team-3'
TEAM = [('health', 'Nurse agent'), ('health', 'Patient educator'), ('health', 'Clinic receptionist'),
        ('support', 'Support agent'), ('support', 'Booking assistant'),
        ('food', 'Café assistant'), ('food', 'Menu writer'),
        ('writing', 'Social media agent'), ('writing', 'Copywriter'),
        ('teach', 'Tutor'), ('teach', "Teacher's assistant"),
        ('business', 'Bookkeeping agent'), ('business', 'Executive assistant'),
        ('plan', 'Event planner'), ('plan', 'Weekly planner'),
        ('trades', 'Handyperson'), ('tech', 'No-code builder'), ('creative', 'UI designer')]
KINDS = [{'species': 'human', 'hairStyle': 1, 'skin': 1, 'hairColor': 1}, {'species': 'dog', 'fur': 7, 'mark': 1, 'markColor': 1, 'brows': 0},
         {'species': 'cat', 'fur': 4, 'mark': 4, 'markColor': 4, 'brows': 1}, {'species': 'human', 'hairStyle': 8, 'skin': 4, 'hairColor': 0},
         {'species': 'duck', 'fur': 8, 'markColor': 7, 'brows': 1}, {'species': 'capybara', 'fur': 5, 'markColor': 3, 'brows': 0}]
backup = json.dumps({'app': 'helpercraft', 'version': 2, 'agents': [
    {'slot': i, 'id': f'e3{i:04d}team', 'thumb': None, 'state': {'name': '', 'role': r, 'specialty': sp, 'hatched': True, 'look': KINDS[i % len(KINDS)]}}
    for i, (r, sp) in enumerate(TEAM)]}).encode()
html = (ROOT / 'helpercraft.html').read_text(encoding='utf-8')
with sync_playwright() as pw:
    b = pw.chromium.launch(channel='chrome')
    ctx = b.new_context(accept_downloads=True)
    ctx.add_init_script('window.showDirectoryPicker = undefined;')   # as in Firefox or Safari: Agent home offers the zip
    ctx.route('http://helpercraft.test/**', lambda route: route.fulfill(body=html, content_type='text/html; charset=utf-8'))
    p = ctx.new_page()
    p.on('dialog', lambda d: d.accept())
    p.goto('http://helpercraft.test/helpercraft.html?nogl')
    p.wait_for_function('() => window.Helpercraft')
    p.set_input_files('#restoreFile', files=[{'name': 'backup.json', 'mimeType': 'application/json', 'buffer': backup}])
    p.wait_for_function("() => /Restored/.test(document.querySelector('#toast').textContent)", timeout=60000)
    if not p.evaluate("() => document.querySelector('#homeDlg').open"):
        p.click('#homeBtn')
    with p.expect_download() as d:
        p.click('#homeDlg [data-act="team-zip"]')
    data = Path(d.value.path()).read_bytes()
    b.close()
shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
z = zipfile.ZipFile(io.BytesIO(data))
root = 'helpercraft-team/'
for n in z.namelist():
    if n.startswith(root) and not n.endswith('/'):
        (OUT / n[len(root):]).parent.mkdir(parents=True, exist_ok=True); (OUT / n[len(root):]).write_bytes(z.read(n))
agents = sorted(p.name for p in (OUT / 'agents').iterdir())
print(len(agents), 'agents:', ', '.join(agents))
assert len(agents) == len(TEAM), agents
