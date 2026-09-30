#!/usr/bin/env python3
"""End-to-end tests for helpercraft.html across browsers, screen sizes, languages and settings.

    python tests/e2e.py                    # everything (about 45 minutes)
    python tests/e2e.py --tiers A          # A: the whole flow in 5 browsers x 2 ways of opening x 3 screens, twice
                                           # L: Chinese and Spanish: the flow, every screen size, switching languages
                                           # B: one setting changed at a time    C: stress, broken input and security
    python tests/e2e.py --tiers A --rounds 1 --engines chrome   # a quick check

Needs Python 3.10+, `pip install playwright pyyaml pillow`, Google Chrome and Microsoft Edge, and Playwright's own
browsers (`python -m playwright install chromium firefox webkit`). Everything runs on this computer: the page is opened
as a file and from a server on 127.0.0.1. Results go to tests/out/: results.json, summary.md, screenshots, downloads.
"""
import argparse, datetime, functools, http.server, json, platform, re, subprocess, sys, threading, time, zipfile
from pathlib import Path

import yaml
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'helpercraft.html'
OUT = ROOT / 'tests' / 'out'
# The page's own #test checks; update when checks are added (each job field adds 2). Pages opened from a file in Chrome
# and Edge get no private test folder, so there the self-test skips its 5 folder checks and says so.
SELFTEST_CHECKS, SELFTEST_FOLDER_CHECKS = 83, 5
CORE_KEYS = {'name', 'description', 'license', 'compatibility', 'metadata'}
EXTRA_KEYS = {'disable-model-invocation', 'user-invocable', 'argument-hint', 'when_to_use', 'paths', 'allowed-tools'}
NAME_RE = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')

# name: (Playwright browser type, launch options). "chromium" stands for a computer without a graphics chip: it draws
# 3D in software (SwiftShader), like a virtual machine, a remote desktop, or hardware acceleration switched off.
ENGINES = {'chromium': ('chromium', {'args': ['--use-angle=swiftshader', '--enable-unsafe-swiftshader']}), 'chrome': ('chromium', {'channel': 'chrome'}),
           'edge': ('chromium', {'channel': 'msedge'}), 'firefox': ('firefox', {}), 'webkit': ('webkit', {})}
PHONE = dict(is_mobile=True, has_touch=True, device_scale_factor=3)
TABLET = dict(is_mobile=True, has_touch=True, device_scale_factor=2)
DEVICES = {
    'phone-360x640': dict(viewport={'width': 360, 'height': 640}, **PHONE),
    'phone-375x667': dict(viewport={'width': 375, 'height': 667}, **PHONE),
    'phone-390x844': dict(viewport={'width': 390, 'height': 844}, **PHONE),
    'phone-412x915': dict(viewport={'width': 412, 'height': 915}, **PHONE),
    'phone-sideways-667x375': dict(viewport={'width': 667, 'height': 375}, **PHONE),
    'phone-sideways-844x390': dict(viewport={'width': 844, 'height': 390}, **PHONE),
    'laptop-1280x720-zoom200': dict(viewport={'width': 640, 'height': 360}, device_scale_factor=2),   # what a 200% zoom leaves
    'tablet-768x1024': dict(viewport={'width': 768, 'height': 1024}, **TABLET),
    'tablet-1024x768': dict(viewport={'width': 1024, 'height': 768}, **TABLET),
    'laptop-1280x720': dict(viewport={'width': 1280, 'height': 720}),
    'laptop-1366x768': dict(viewport={'width': 1366, 'height': 768}),
    'laptop-1440x900': dict(viewport={'width': 1440, 'height': 900}),
    'desktop-1920x1080': dict(viewport={'width': 1920, 'height': 1080}),
    'desktop-2560x1440': dict(viewport={'width': 2560, 'height': 1440}),
}
TIER_A_DEVICES = ['phone-390x844', 'laptop-1440x900', 'desktop-1920x1080']
LANGS = {'zh': 'zh-TW', 'es': 'es-ES'}   # language: the browser language that should pick it

# Every page gets a clipboard that records what the app copies, so Copy can be checked.
INIT = """
window.__copied = [];
addEventListener('error', e => { window.__broken = String(e.message); });
try { Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText: async t => { window.__copied.push(String(t)); } } }); } catch (e) {}
"""
IPHONE_UA = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'
# A stand-in for the phone's share sheet, which needs a person: it records what the app shares
SHARE = """
window.__shared = [];
navigator.share = async data => {
  if (window.__shareFail) throw new DOMException('Sharing failed', window.__shareFail);
  window.__shared.push({ title: data.title || '', text: data.text || '', files: await Promise.all((data.files || []).map(async f => ({ name: f.name, type: f.type, text: await f.text() }))) });
};
navigator.canShare = () => true;
"""
# What Chrome does when a person blocks site data: touching localStorage throws.
BLOCK_STORAGE = """
Object.defineProperty(window, 'localStorage', { configurable: true, get() { throw new DOMException('Access is denied for this document.', 'SecurityError'); } });
"""
LEGACY = {'step': 2, 'hatched': False, 'bornAt': None, 'name': 'Nova', 'id': None, 'slot': None, 'role': 'health', 'specialty': 'Nurse agent',
          'customTitle': '', 'tasks': None, 'customTasks': [], 'audience': 'team', 'workplace': '', 'archetype': 'sunny',
          'traits': {'warmth': 85, 'energy': 80, 'humor': 55, 'detail': 40}, 'emoji': False, 'catchphrase': '', 'home': 'claude',
          'look': {'species': 'human', 'skin': 1, 'hairStyle': 0, 'hairColor': 1, 'eyes': 0, 'glasses': 0, 'outfit': 0, 'fur': 2, 'mark': 0,
                   'markColor': 2, 'brows': 2, 'extras': [], 'build': 1}}
SEED_LEGACY = "if (!sessionStorage.getItem('seeded')) { sessionStorage.setItem('seeded', '1'); localStorage.setItem('helpercraft.v2', %s); }" % json.dumps(json.dumps(LEGACY))   # a save from an older version: a setting since dropped (home), and none of the newer ones

READY = "() => document.documentElement.classList.contains('no-webgl') || (window.Stage && Stage.ready)"
BANNER = "() => [...document.querySelectorAll('body > div')].map(d => d.textContent).find(t => /^Self-test/.test(t)) || ''"
FPS = """() => new Promise(r => { let n = 0; const t0 = performance.now();
  const f = () => { n++; if (performance.now() - t0 < 2000) requestAnimationFrame(f); else r(Math.round(n * 1000 / (performance.now() - t0))); }; requestAnimationFrame(f); })"""
RENDERER = """() => { const c = document.createElement('canvas').getContext('webgl2'), d = c && c.getExtension('WEBGL_debug_renderer_info');
  return c ? (d ? c.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl2') : 'none'; }"""


# Every finished run is written to results.json at once, so a browser that hangs on its way out can't take the rest
PROGRESS = {'meta': {}, 'runs': []}


def save_progress():
    PROGRESS['meta']['minutes'] = round((time.time() - PROGRESS['meta'].get('start', time.time())) / 60, 1)
    (OUT / 'results.json').write_text(json.dumps(PROGRESS, indent=1, ensure_ascii=False), encoding='utf-8')


def close(browser):
    if browser.browser_type.name == 'webkit':
        return   # WebKit on Windows sometimes never finishes closing; Playwright ends it when the run ends
    try:
        browser.close()
    except Exception as e:
        print(f"  (the browser didn't close cleanly: {str(e).splitlines()[0]})", flush=True)


def launch(pw, eng, **kw):
    kind, opts = ENGINES[eng]
    bt = getattr(pw, kind)
    if not opts:   # Playwright's own browsers start from their real folder: run from a packaged Windows app, AppData is
        opts = {'executable_path': str(Path(bt.executable_path).resolve())}   # redirected and Firefox can't load its libraries
    return bt.launch(headless=True, **opts, **kw)


# ---------- one environment ----------
class Run:
    """A fresh browser context (nothing carries over between environments) and everything it logs."""

    def __init__(self, browser, env, device, url, init=(), **ctx):
        self.env, self.device, self.url, self.checks, self.facts = env, device, url, [], {}
        opts = {**DEVICES[device], 'locale': 'en-US', **ctx}   # English unless a run asks for another language
        if browser.browser_type.name == 'firefox':
            opts.pop('is_mobile', None)   # Firefox can't pretend to be a phone browser; the size and touch still apply
        self.ctx = browser.new_context(accept_downloads=True, **opts)
        for s in (INIT, *init):
            self.ctx.add_init_script(s)
        self.page = p = self.ctx.new_page()
        p.set_default_timeout(20000)
        p.set_default_navigation_timeout(90000)   # without a graphics chip, the 3D view can hold up the page for a while
        self.errors, self.console, self.requests, self.dialogs = [], [], [], []
        p.on('pageerror', lambda e: self.errors.append(str(e)))
        p.on('console', lambda m: self.console.append(m.text) if m.type == 'error' else None)
        p.on('request', lambda r: self.requests.append(r.url))
        p.on('dialog', lambda d: (self.dialogs.append(d.message), d.accept()))

    def check(self, name, ok, detail=''):   # ok: True, False, or None when it couldn't be tested here
        self.checks.append({'check': name, 'ok': ok, 'detail': detail if isinstance(detail, str) else json.dumps(detail, ensure_ascii=False)})
        return ok

    def open(self, query=''):
        if 'still' not in query:   # keep the 3D moving: a busy test computer mustn't switch to the still picture
            query += ('&' if '?' in query else '?') + 'still=off'
        t = time.time()
        self.page.goto(self.url + query)
        self.page.wait_for_function("() => document.querySelector('#panelBody h2') || window.__broken", timeout=90000)
        if broken := self.page.evaluate('() => window.__broken'):
            raise RuntimeError(f'the page failed to start: {broken}')
        self.page.wait_for_function(READY, timeout=180000)
        self.facts.setdefault('open and 3D ready (s)', round(time.time() - t, 1))

    def t(self, s, **p):   # the app's own text in its current language
        return self.page.evaluate('([s, p]) => Helpercraft.T(s, p)', [s, p or None])

    def shot(self, name):
        path = OUT / 'shots' / f'{self.env}--{self.device}--{name}.png'
        self.page.screenshot(path=str(path), scale='css')
        return path

    def attempt(self, fn, *a):
        try:
            fn(*a)
        except Exception as e:
            lines = str(e).splitlines()
            self.check('run finished', False, ' '.join([f'{type(e).__name__}: {lines[0]}', *[l.strip() for l in lines if 'waiting for' in l][:1]]))

    def result(self):
        return {'env': self.env, 'device': self.device, 'checks': self.checks, 'facts': self.facts}

    def close(self):
        try:
            self.ctx.close()
        except Exception as e:
            self.check('the browser window closed', False, str(e).splitlines()[0])
        PROGRESS['runs'].append(self.result())
        save_progress()
        good = sum(c['ok'] is True for c in self.checks)
        print(f'  {self.env} {self.device}: {good}/{len(self.checks)} passed', flush=True)


def load_checks(run):
    bad = [c for c in run.console if 'favicon' not in c]
    run.check('no errors on the page', not run.errors and not bad, '; '.join(run.errors + bad)[:600])


def network_check(run):
    base = run.url.split('?')[0]
    seen = [u.split('#')[0].split('?')[0] for u in run.requests]
    other = [u for u in seen if u != base and not u.startswith(('data:', 'blob:'))]
    if base not in seen:   # the page's own request is the control: without it, "nothing else" proves nothing
        return run.check('nothing loaded from the network', None, 'requests aren’t visible for this kind of page')
    icon = [u for u in other if u.endswith('/favicon.ico')]
    if icon:
        run.facts['browser asked the server for favicon.ico'] = True
    run.check('nothing loaded from the network', not [u for u in other if u not in icon], ', '.join(other))


LAYOUT_JS = """() => {
  const q = s => document.querySelector(s);
  const vis = e => { if (!e) return false; const cs = getComputedStyle(e), b = e.getBoundingClientRect();
    return cs.display !== 'none' && cs.visibility !== 'hidden' && b.width > 0 && b.height > 0 && b.left >= -1 && b.top >= -1 && b.right <= innerWidth + 1 && b.bottom <= innerHeight + 1; };
  const foot = [...document.querySelectorAll('#panelFoot button')].map(b => b.getBoundingClientRect().height);
  const panel = q('.panel').getBoundingClientRect(), dock = q('#dock'), box = s => q(s).getBoundingClientRect();
  const hits = (a, b) => a.width && b.width && a.left < b.right && b.left < a.right && a.top < b.bottom && b.top < a.bottom;
  const tops = ['.brand', '#privacyBtn', '#homeBtn', '#lang', '#filePill'].filter(s => getComputedStyle(q(s)).display !== 'none').map(box);
  const out = { w: innerWidth, h: innerHeight, side: panel.left > 20, overflowX: document.documentElement.scrollWidth - innerWidth,
    panel: vis(q('.panel')), tabs: vis(q('#steps')), foot: vis(q('#panelFoot')), footMin: Math.min(...foot), name: vis(q('#npName')) && (!q('#npRole').textContent.trim() || vis(q('#npRole'))), lang: vis(q('#lang')),
    langClash: tops.some((a, i) => tops.some((b, j) => i < j && hits(a, b))) || hits(box('#lang'), panel),
    bubble: !q('#bubble').classList.contains('hide'), bubbleClash: tops.some(t => hits(t, box('#bubble'))),
    panelLeft: panel.left, panelTop: panel.top, dockRight: dock.getClientRects().length ? dock.getBoundingClientRect().right : 0 };
  if (window.Stage && Stage.ready) {
    const head = Stage.worldToScreen(Stage.headTop()), feet = Stage.worldToScreen([0, -0.3, 1.1]);
    Object.assign(out, { headX: head[0], headY: head[1], feetX: feet[0], feetY: feet[1] });
  }
  return out;
}"""
# Words too long for their box: tabs, buttons, chips and tiles whose text sticks out, or footer buttons that grew a line
CLIPPED_JS = """() => [...document.querySelectorAll('.step-tab, .top-actions button, .lang button, #panelFoot .btn, #panelBody .btn, #panelBody .chip, #panelBody .tile, #panelBody .kind, #panelBody .seg button, #panelBody .zodiac button, #teamBar .btn, .home-foot .btn')]
  .filter(e => e.getClientRects().length && (e.scrollWidth > e.clientWidth + 1 || (e.closest('#panelFoot') && e.scrollHeight > e.clientHeight + 1)))
  .map(e => e.textContent.trim().replace(/\\s+/g, ' ').slice(0, 40))"""


def layout_checks(run):
    run.page.evaluate('() => Helpercraft.say()')   # a speech bubble to check too
    run.page.wait_for_timeout(1200)   # the character eases into place
    m = run.page.evaluate(LAYOUT_JS)
    run.check('no sideways scrolling', m['overflowX'] <= 0, f"{m['overflowX']}px too wide")
    run.check('panel, step tabs and buttons on screen', m['panel'] and m['tabs'] and m['foot'], {k: m[k] for k in ('panel', 'tabs', 'foot')})
    run.check('buttons at least 24px tall', m['footMin'] >= 24, f"{m['footMin']:.0f}px")
    run.check('agent’s name (and its job tag, when it has a name) on screen', m['name'])
    run.check('logo, pills and language switch on screen, covering nothing', m['lang'] and not m['langClash'])
    run.check('speech bubble clear of the logo and pills', m['bubble'] and not m['bubbleClash'])
    run.facts['layout'] = 'side by side' if m['side'] else 'stacked'
    if 'headX' in m:
        if not m['side']:
            gap = m['panelTop'] - m['feetY']
            run.facts['pedestal to panel (px)'] = round(gap)
            run.check('character above the panel, head on screen', m['headY'] > 0 and -8 <= gap <= 40, f"head at y {m['headY']:.0f}, pedestal ends {gap:.0f}px above the panel")
        else:
            left, right = m['dockRight'], m['panelLeft']
            run.check('character between the file card and the panel', left + 60 <= m['feetX'] <= right - 60 and m['headY'] > 0,
                      f"feet at x {m['feetX']:.0f}, free room {left:.0f}–{right:.0f}")
    return m


# Text on screen: the smallest size, and any words too faint to read (4.5 to 1, or 3 to 1 for large text). The job tag
# under the name is left out: it's small on purpose (9.6px capitals, the owner's choice). Text over a picture or a
# gradient is skipped for contrast, since its background can't be read from the styles.
TEXT_JS = """() => {
  const out = { min: 99, minText: '', faint: [] };
  const lum = c => { const v = c.map(x => { x /= 255; return x <= 0.04045 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }); return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]; };
  const rgba = s => { const m = s.match(/[\\d.]+/g).map(Number); return [m.slice(0, 3), m.length > 3 ? m[3] : 1]; };
  const over = (top, a, base) => top.map((t, i) => a * t + (1 - a) * base[i]);
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    const e = n.parentElement, t = n.nodeValue.trim();
    if (!t || !e || e.closest('script, style, option, dialog:not([open]), [disabled], #npRole')) continue;
    if (!e.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) continue;
    const r = document.createRange(); r.selectNodeContents(n);
    const q = [...r.getClientRects()].find(q => q.width > 1 && q.top >= 0 && q.bottom <= innerHeight && q.left >= 0 && q.right <= innerWidth);
    if (!q) continue;
    if (!e.closest('.overlay')) { const h = document.elementFromPoint((q.left + q.right) / 2, (q.top + q.bottom) / 2); if (!h || !(e.contains(h) || h.contains(e))) continue; }
    const cs = getComputedStyle(e), size = parseFloat(cs.fontSize) * (e.currentCSSZoom || 1);
    if (size < out.min) { out.min = size; out.minText = t.slice(0, 30); }
    let [fg, fa] = rgba(cs.color), layers = [], base = null, op = 1;
    for (let a = e; a; a = a.parentElement) {
      const st = getComputedStyle(a); op *= parseFloat(st.opacity);
      if (st.backgroundImage !== 'none') break;
      const [c, al] = rgba(st.backgroundColor);
      if (al >= 1) { base = c; break; }
      if (al > 0) layers.push([c, al]);
    }
    if (!base) continue;
    for (const [c, al] of layers.reverse()) base = over(c, al, base);
    const col = over(fg, fa * op, base), L1 = lum(col), L2 = lum(base);
    const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    if (ratio < (size >= 24 || (size >= 18.66 && +cs.fontWeight >= 700) ? 3 : 4.5)) out.faint.push(`${t.slice(0, 30)} (${ratio.toFixed(2)})`);
  }
  return out;
}"""


STRAY_JS = r"() => document.body.innerText.match(/\b(null|undefined|NaN)\b/g) || []"


def tour(run):
    """Every step, then the file preview: nothing sticks out of its box, no text under 10px, nothing too faint to read,
    no stray "null" (also in Agent home), and (in Chinese and Spanish) nothing untranslated."""
    p, clipped, smallest, faint, stray = run.page, {}, (99, ''), {}, set()
    for i in range(6):
        p.click(f'.step-tab >> nth={i}')
        stray |= set(p.evaluate(STRAY_JS))
        for text in p.evaluate(CLIPPED_JS):
            clipped.setdefault(text, i + 1)
        m = p.evaluate(TEXT_JS)
        smallest = min(smallest, (round(m['min'], 1), f"{m['minText']} (step {i + 1})"))
        for f in m['faint']:
            faint.setdefault(f, i + 1)
    p.click('#filePill') if p.is_visible('#filePill') else p.click('#dockToggle')
    p.evaluate("() => { const d = document.querySelector('#fileDlg'); if (d.open) d.close(); }")
    p.click('.step-tab >> nth=0')   # back to the start
    p.click('#homeBtn'); stray |= set(p.evaluate(STRAY_JS)); p.evaluate("() => document.querySelector('#homeDlg').close()")
    run.check('no stray “null” or “undefined” on screen (all 6 steps and Agent home)', not stray, sorted(stray))
    run.check('no words cut off in tabs, buttons, chips or tiles (all 6 steps)', not clipped, {k: f'step {v}' for k, v in list(clipped.items())[:8]})
    run.facts['smallest text (px)'] = smallest[0]
    run.check('no text smaller than 10px (all 6 steps)', smallest[0] >= 10, f'{smallest[0]}px: {smallest[1]}')
    run.check('all text readable: contrast 4.5 to 1 or more (all 6 steps)', not faint, {k: f'step {v}' for k, v in list(faint.items())[:8]})


def missing_check(run):
    miss = run.page.evaluate('() => [...Helpercraft.missing]')
    run.check('nothing left untranslated on the screens visited', not miss, miss[:6])


def selftest(run):
    run.page.goto(run.url + '?selftest=1#test')
    run.page.wait_for_function(BANNER, timeout=180000)
    text = run.page.evaluate(BANNER)
    skipped = 'skipped' in text
    m, want = re.search(r'all (\d+) checks passed', text), SELFTEST_CHECKS - (SELFTEST_FOLDER_CHECKS if skipped else 0)
    run.check(f'built-in self-test ({want} checks)', bool(m) and int(m.group(1)) == want and (skipped or not run.url.startswith('file:') or 'firefox' in run.env or 'webkit' in run.env), text)


# ---------- the files the app makes ----------
def frontmatter(text):
    if not text.startswith('---\n'):
        raise ValueError('no frontmatter')
    return text[4:text.index('\n---\n', 4)]


def roundtrip(fm, data):
    """Every quoted value was written as JSON; YAML must read back exactly what the JSON meant."""
    out, parent = [], None
    for line in fm.split('\n'):
        m = re.match(r'^( *)([\w-]+):(?: (.*))?$', line)
        if not m:
            continue
        indent, key, raw = m.groups()
        if not indent:
            parent = key if raw is None else None
        if not raw or not raw.startswith(('"', '[')):
            continue
        try:
            want = json.loads(raw)
        except ValueError:
            out.append(f'{key}: not one JSON value')
            continue
        got = (data.get(parent) or {}).get(key) if indent else data.get(key)
        if got != want:
            out.append(f'{key}: YAML reads {got!r}, JSON meant {want!r}')
    return out


def skill_problems(text, allowed, desc_max=200):
    try:
        fm = frontmatter(text)
        data = yaml.safe_load(fm)
    except Exception as e:
        return [f'YAML error: {str(e).splitlines()[0]}']
    if not isinstance(data, dict):
        return ['frontmatter isn’t a list of settings']
    probs = []
    if set(data) - allowed:
        probs.append(f'unexpected settings {sorted(set(data) - allowed)}')
    name, desc = data.get('name'), data.get('description')
    if not (isinstance(name, str) and NAME_RE.match(name) and len(name) <= 64):
        probs.append(f'bad name {name!r}')
    if not (isinstance(desc, str) and 0 < len(desc) <= desc_max and not set('<>') & set(desc)):
        probs.append(f'bad description ({len(desc or "")} characters)')
    elif re.search('[\ud800-\udfff]', desc):
        probs.append('description has half a character (a split emoji)')
    return probs + roundtrip(fm, data)


def zip_problems(path, folder, core_only):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if f'{folder}/SKILL.md' not in names:
            return [f'no {folder}/SKILL.md in {names}']
        probs = [f'stray entry {n}' for n in names if not n.startswith(f'{folder}/')]
        if z.testzip() is not None:
            probs.append('damaged zip (CRC)')
        text = z.read(f'{folder}/SKILL.md').decode('utf-8')
    probs += skill_problems(text, CORE_KEYS if core_only else CORE_KEYS | EXTRA_KEYS)
    if not probs and yaml.safe_load(frontmatter(text)).get('name') != folder:
        probs.append('the name inside differs from the folder')
    return probs


def save(download, run, tag):
    path = OUT / 'downloads' / f'{run.env}--{run.device}--{tag}--{download.suggested_filename}'
    download.save_as(str(path))
    return path


def file_safe(s):   # the app's rule for the downloaded file's name
    return re.sub(r'^\.+|\.+$', '', re.sub(r'\s+', '-', re.sub(r'[\\/:*?"<>|\x00-\x1f]', '', s).strip()))[:40]


# ---------- the whole flow, clicked the way a person would (in whatever language the page is in) ----------
def flow(run, name='Pip'):
    p = run.page
    p.fill('#panelBody .name-input', name)
    p.click('button.kind:has(.kind-pic[data-kind="dog"])')
    p.click('.step-tab >> nth=1')
    p.click('.tile[data-role="health"]')
    p.click('.step-tab >> nth=2')
    p.click('.tile[data-arch="mentor"]')
    p.click('.step-tab >> nth=3')
    p.click('label.check[data-k="flow"]')
    p.click('.step-tab >> nth=5')
    p.click('#panelFoot [data-act="hatch"]')
    p.wait_for_selector('.cert h2')
    run.check('make and craft an agent (name, dog, job, personality, habit)', p.inner_text('.cert h2') == run.t('Welcome, {n}!', n=name), p.inner_text('.cert h2'))
    slug = p.inner_text('.cert dd .mono').split('/')[0]
    p.click('[data-act="copy"]')
    copied = p.evaluate('() => window.__copied.at(-1) || ""')
    run.check('Copy gives ready-to-paste instructions with the choices in them', copied.startswith(run.t('From now on in this chat, be the agent described below.'))
              and '\nname: ' not in copied and run.t('a fluffy cartoon Pomeranian: loyal and eager to help') in copied and 'Mermaid' in copied, copied[:90])
    with p.expect_download() as d:
        p.click('[data-act="md"]')
    md = save(d.value, run, 'md')
    want = f"{name}_{file_safe(run.t('Nurse agent'))}_Skill.md"
    run.check('.md download is named Name_Job_Skill.md', d.value.suggested_filename == want, f'{d.value.suggested_filename} (wanted {want})')
    text = md.read_text(encoding='utf-8')
    english_left = run.page.evaluate('() => Helpercraft.lang') != 'en' and any(h in text for h in ('## Who you are', '## How you talk', 'Use when the user'))
    run.check('.md file is a valid skill, in the page’s language', not (pr := skill_problems(text, CORE_KEYS | EXTRA_KEYS)) and not english_left, '; '.join(pr) or ('English left in the file' if english_left else ''))
    with p.expect_download() as d:
        p.click('[data-act="claude-zip"]')
    run.check('Claude app zip is valid, portable settings only', not (pr := zip_problems(save(d.value, run, 'claude'), slug, True)), '; '.join(pr))
    p.click('details.more > summary')
    with p.expect_download() as d:
        p.click('[data-act="tools-zip"]')
    run.check('coding-tools zip is valid', not (pr := zip_problems(save(d.value, run, 'tools'), slug, False)), '; '.join(pr))
    run.check('the new agent is in Agent home', p.inner_text('#homeCount') == '1', p.inner_text('#homeCount'))


# ---------- tier A: the whole flow everywhere ----------
def tier_a(pw, urls, rounds, engines):
    results = []
    for rnd in range(1, rounds + 1):
        for eng in engines:
            browser = launch(pw, eng)
            for load, url in urls.items():
                for dev in TIER_A_DEVICES:
                    run = Run(browser, f'A{rnd}-{eng}-{load}', dev, url)

                    def go():
                        run.open()
                        run.facts['3D'] = run.page.evaluate(RENDERER)
                        run.facts['frames per second'] = run.page.evaluate(FPS)
                        run.facts['3D quality'] = run.page.evaluate('() => window.Stage ? Stage.quality : null')
                        layout_checks(run)
                        if rnd == 1:
                            run.shot('start')
                        flow(run)
                        if rnd == 1:
                            run.shot('hatched')
                        load_checks(run)
                        network_check(run)
                        selftest(run)
                    run.attempt(go)
                    results.append(run.result())
                    run.close()
            close(browser)
    return results


# ---------- tier L: Chinese and Spanish ----------
def tier_l(pw, urls):
    results, url = [], urls['file']
    chrome = launch(pw, 'chrome')

    def one(env, device, extra, **ctx):
        run = Run(chrome, env, device, url, **ctx)
        run.attempt(extra, run)
        results.append(run.result())
        run.close()

    for lang, locale in LANGS.items():
        def whole(run, lang=lang):   # opens in the browser's language, then the whole flow and the self-test
            run.open()
            run.check(f'the page picks {lang} from the browser’s language', run.page.evaluate('() => [Helpercraft.lang, document.documentElement.lang]') == [lang, {'zh': 'zh-Hant', 'es': 'es'}[lang]])
            layout_checks(run)
            run.shot('start')
            tour(run)
            flow(run)
            run.shot('hatched')
            run.page.click('#homeBtn')
            run.page.click('#room .slot:not(.empty)')
            run.shot('home')
            missing_check(run)
            load_checks(run)
            selftest(run)
        for dev in TIER_A_DEVICES:
            one(f'L-{lang}', dev, whole, locale=locale)

        def screen(run):
            run.open()
            layout_checks(run)
            tour(run)
            run.shot('start')
            missing_check(run)
            load_checks(run)
        for dev in DEVICES:
            if dev not in TIER_A_DEVICES:
                one(f'L-{lang}-screen', dev, screen, locale=locale)

    def switch(run):   # English page; switch live, see everything follow, and the choice stick after a reload
        p = run.page
        run.open()
        tab = lambda: p.inner_text('.step-tab >> nth=0').split('\n')[-1].strip()   # the label, without the step number
        start = (run.page.evaluate('() => Helpercraft.lang'), tab())
        p.click('#lang button[data-lang="zh"]')
        zh = (run.page.evaluate('() => [Helpercraft.lang, document.documentElement.lang]'), tab(), p.inner_text('#privacyBtn'))
        run.check('C switches the page to Chinese at once', start == ('en', 'Name') and zh[0] == ['zh', 'zh-Hant'] and zh[1] != 'Name' and 'Private' not in zh[2], [start, zh])
        flow(run)
        p.reload()
        p.wait_for_selector('#panelBody h2')
        run.check('…and it stays Chinese after a reload', run.page.evaluate('() => Helpercraft.lang') == 'zh')
        p.click('#lang button[data-lang="es"]')
        p.click('#homeBtn')
        sub = p.inner_text('#homeSub')
        run.check('S switches to Spanish, open windows included', run.page.evaluate('() => Helpercraft.lang') == 'es' and sub == run.t('Room {room} of {rooms} · 1 agent at home', room=1, rooms=20), sub)
        p.keyboard.press('Escape')
        p.click('#lang button[data-lang="en"]')
        run.check('E brings English back', tab() == 'Name' and 'Private' in p.inner_text('#privacyBtn'))
        missing_check(run)
        load_checks(run)
    one('L-switch', 'laptop-1440x900', switch)
    one('L-switch', 'phone-390x844', switch)
    close(chrome)
    return results


# ---------- tier B: one setting at a time ----------
def contrast(path, box):
    """Contrast ratio between the darkest and lightest tenth of the pixels in a box: text against its background."""
    im = Image.open(path).convert('RGB').crop(tuple(round(v) for v in box))
    lum = sorted(0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b) for r, g, b in im.get_flattened_data())
    k = max(1, len(lum) // 10)
    dark, light = sum(lum[:k]) / k, sum(lum[-k:]) / k
    return (light + 0.05) / (dark + 0.05), light


def lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def still_picture(run):   # every frame "takes" 150 ms, under 7 a second: a computer too slow for the 3D
    p = run.page
    changed = lambda a, b: ImageChops.difference(a, b).convert('L').point(lambda v: 255 if v > 24 else 0).histogram()[255]
    p.evaluate('() => Stage.simulateSlow(150)')
    t = time.time()
    p.wait_for_function('() => Stage.still', timeout=90000)
    run.facts['switched to the still picture after (s)'] = round(time.time() - t, 1)
    note = p.inner_text('#toast')
    saved = p.evaluate("() => JSON.parse(localStorage.getItem('helpercraft.still'))")
    run.check('under 10 frames a second: the still picture, with a one-time note', note == run.t('3D paused to keep things smooth on this computer.'), note)
    days = (saved['until'] / 1000 - time.time()) / 86400 if saved else 0
    run.check('remembered in this browser for 7 days', 6.9 < days <= 7.01, f'{days:.2f} days')
    p.add_style_tag(content='.overlay, .toast { visibility: hidden !important; } .glow::before { display: none !important; }')   # just the character
    box = p.evaluate("() => [0, 0, Math.round(document.querySelector('.panel').getBoundingClientRect().left), innerHeight]")
    p.wait_for_timeout(600)
    a = Image.open(run.shot('still-1')).convert('RGB').crop(box)
    p.wait_for_timeout(1500)
    b = Image.open(run.shot('still-2')).convert('RGB').crop(box)
    run.check('the character stands still', changed(a, b) < 50, f'{changed(a, b)} pixels changed in 1.5 s')
    p.click('.swatch >> nth=3')   # another skin tone
    p.wait_for_timeout(800)
    c = Image.open(run.shot('still-3')).convert('RGB').crop(box)
    run.check('a change shows at once', changed(b, c) > 500, f'{changed(b, c)} pixels changed')
    x, y = box[2] // 2, box[3] // 2   # drag across the character: it spins, then stands still again
    p.mouse.move(x - 80, y); p.mouse.down(); p.mouse.move(x + 80, y, steps=12); p.mouse.up()
    p.wait_for_timeout(800)
    d = Image.open(run.shot('still-4')).convert('RGB').crop(box)
    p.wait_for_timeout(1500)
    e = Image.open(run.shot('still-5')).convert('RGB').crop(box)
    run.check('dragging spins it, then it stands still again', changed(c, d) > 500 and changed(d, e) < 50, f'{changed(c, d)} pixels changed by the drag, {changed(d, e)} after')
    p.reload()
    p.wait_for_function(READY, timeout=180000)
    p.wait_for_timeout(500)
    again = p.evaluate("() => [Stage.still, document.querySelector('#toast').classList.contains('show')]")
    run.check('the next visit starts with the still picture, without the note', again == [True, False], again)


# High contrast removes background colours and shadows. Each chosen thing must still look different from unchosen:
# switch it off for a moment and compare the two pictures.
CHOSEN_JS = """() => {
  const sel = ['.step-tab[aria-selected="true"]', '.kind[aria-checked="true"]', '.swatch[aria-checked="true"]', '.chip[aria-checked="true"]',
    '.lang button[aria-checked="true"]', '.stats .pip.on'];
  window.__chosen = sel.map(s => [...document.querySelectorAll(s)].find(e => e.checkVisibility() && e.getBoundingClientRect().width)).filter(Boolean);
  return window.__chosen.map(e => { const q = e.getBoundingClientRect(); return [e.className || e.tagName, [q.left - 6, q.top - 6, q.right + 6, q.bottom + 6].map(Math.round)]; });
}"""
FLIP_JS = """([i, on]) => { const e = window.__chosen[i];
  for (const a of ['aria-checked', 'aria-selected']) if (e.hasAttribute(a)) e.setAttribute(a, String(on));
  if (e.classList.contains('pip') || e.dataset.wasOn) { e.classList.toggle('on', on); e.dataset.wasOn = '1'; } }"""


def chosen_marks(run):
    p, hidden = run.page, []
    p.click('.step-tab >> nth=0')
    p.wait_for_timeout(400)
    marks = p.evaluate(CHOSEN_JS)
    for i, (what, box) in enumerate(marks):
        before = Image.open(run.shot('chosen')).convert('RGB').crop(box)
        p.evaluate(FLIP_JS, [i, False]); p.wait_for_timeout(350)
        after = Image.open(run.shot('chosen')).convert('RGB').crop(box)
        p.evaluate(FLIP_JS, [i, True]); p.wait_for_timeout(350)
        if ImageChops.difference(before, after).convert('L').point(lambda v: 255 if v > 24 else 0).histogram()[255] < 12:
            hidden.append(what.split(' ')[0])
    run.check('chosen things still show: step, kind, colour dot, chip, language, personality bar', len(marks) >= 5 and not hidden,
              f"{len(marks)} checked, hidden: {', '.join(hidden) or 'none'}")


def tier_b(pw, urls, only=None):   # only: a set of run names, to re-run just those
    results, url = [], urls['file']
    chrome = launch(pw, 'chrome')

    def one(env, device='laptop-1440x900', browser=chrome, init=(), query='', extra=None, cdp=None, url=url, **ctx):
        if only and env not in only:
            return
        run = Run(browser, env, device, url, init=init, **ctx)

        def go():
            if cdp:
                cdp(run)
            run.open(query)
            layout_checks(run)
            run.shot('start')
            if extra:
                extra(run)
            load_checks(run)
        run.attempt(go)
        results.append(run.result())
        run.close()

    for dev in DEVICES:
        if dev not in TIER_A_DEVICES:
            one('B-screen', dev, extra=tour)

    def name_tag(run):
        box = run.page.evaluate("() => { const b = document.querySelector('#npName').getBoundingClientRect(); return [b.left, b.top, b.right, b.bottom]; }")
        ratio, _ = contrast(run.shot('name'), box)
        run.check('agent’s name readable (contrast 4.5 or more)', ratio >= 4.5, f'{ratio:.1f}')

    def dot_colour(run):   # high contrast and forced dark repaint plain background colours, so the dots are drawn on canvases
        x, y = run.page.evaluate("() => { const d = document.querySelector('.swatch .dot'); d.scrollIntoView({ block: 'center' }); const b = d.getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; }")
        run.page.wait_for_timeout(400)
        px = Image.open(run.shot('dots')).convert('RGB').getpixel((round(x), round(y)))
        run.check('colour dots keep their real colours (the palest skin tone)', max(abs(a - b) for a, b in zip(px, (0xf7, 0xd7, 0xc0))) <= 12, '#%02x%02x%02x' % px)
    one('B-dark-mode', 'phone-390x844', color_scheme='dark', extra=name_tag)
    one('B-high-contrast', forced_colors='active', extra=lambda run: (name_tag(run), dot_colour(run), chosen_marks(run)))

    def motion(run):
        glow = run.page.evaluate("() => { const s = getComputedStyle(document.querySelector('.glow'), '::before'); return [s.animationName, s.display]; }")
        run.check('reduced motion: no light round the file button, moving or still', glow == ['none', 'none'], glow)
        flow(run)
    one('B-reduced-motion', reduced_motion='reduce', extra=motion)
    one('B-no-3D', query='?nogl', extra=lambda run: (run.check('3D switched off, the app still works', run.page.evaluate(
        "() => document.documentElement.classList.contains('no-webgl')")), flow(run)))
    one('B-language-we-dont-have-and-time-zone', locale='de-DE', timezone_id='Asia/Tokyo',
        extra=lambda run: (run.check('a German browser gets English', run.page.evaluate('() => Helpercraft.lang') == 'en'), flow(run)))

    def slow(run):
        run.facts['frames per second'] = run.page.evaluate(FPS)
        run.facts['3D quality'] = run.page.evaluate('() => Stage.quality')
        flow(run)
    one('B-slow-phone-cpu-x6', 'phone-360x640', extra=slow,
        cdp=lambda run: run.ctx.new_cdp_session(run.page).send('Emulation.setCPUThrottlingRate', {'rate': 6}))

    def share(run):
        p = run.page
        p.fill('#panelBody .name-input', 'Poppy')
        p.click('.step-tab >> nth=5')
        p.click('#panelFoot [data-act="hatch"]')
        p.wait_for_selector('.cert h2')
        p.click('[data-act="share"]')
        p.wait_for_function('() => window.__shared.length === 1')
        s = p.evaluate('() => window.__shared[0]')
        run.check('Share sends the ready-to-paste instructions', s['text'].startswith('From now on in this chat') and 'Poppy' in s['title'], s['title'])
        p.evaluate("() => { window.__shareFail = 'NotAllowedError'; }")
        with p.expect_download() as d:
            p.click('[data-act="share"]')
        run.check('if sharing isn’t allowed, the file downloads instead', d.value.suggested_filename == 'Poppy_Agent_Skill.md', d.value.suggested_filename)
        p.evaluate('() => { window.__shareFail = null; }')
        p.click('#homeBtn')
        p.click('#backupBtn')
        p.wait_for_function('() => window.__shared.length === 2')
        f = (p.evaluate('() => window.__shared[1].files') or [{}])[0]
        run.check('the backup is shared as a plain-text .txt (the kind Android shares)', f.get('name', '').endswith('.txt') and f.get('type') == 'text/plain', f"{f.get('name')} {f.get('type')}")
        desk = run.ctx.browser.new_context(**DEVICES['laptop-1440x900'], locale='en-US')   # the computer it was emailed to
        dp = desk.new_page()
        dp.on('dialog', lambda dlg: dlg.accept())
        dp.goto(run.url)
        dp.wait_for_selector('#panelBody h2')
        dp.set_input_files('#restoreFile', files=[{'name': f.get('name', 'x.txt'), 'mimeType': 'text/plain', 'buffer': f.get('text', '').encode()}])
        dp.wait_for_function("() => /Restored|isn’t a Helpercraft/.test(document.querySelector('#toast').textContent)")
        run.check('…and restores on a computer', dp.inner_text('#homeCount') == '1', dp.inner_text('#toast'))
        desk.close()
    one('B-phone-share-sheet', 'phone-390x844', init=[SHARE], extra=share)

    def blocked(run):
        p = run.page
        p.fill('#panelBody .name-input', 'Wren')
        p.click('.step-tab >> nth=5')
        p.click('#panelFoot [data-act="hatch"]')
        p.wait_for_selector('.cert h2')
        toast = p.inner_text('#toast')
        run.check('with saving blocked: hatches, and says why they can’t be kept', 'blocked' in toast and 'out of space' not in toast, toast)
        p.click('[data-act="copy"]')
        run.check('…and Copy still works', p.evaluate('() => window.__copied.length') == 1)
        p.click('#lang button[data-lang="es"]')
        run.check('…and the language switch works without saving', p.evaluate('() => Helpercraft.lang') == 'es' and not run.errors)
    one('B-saving-blocked', init=[BLOCK_STORAGE], extra=blocked)

    def legacy(run):
        p = run.page
        before = p.inner_text('#npName')
        p.click('.step-tab >> nth=0')
        p.click('button.linkbtn:has-text("Start fresh")')
        after = p.inner_text('#npName')
        p.reload()
        p.wait_for_selector('#panelBody h2')
        now = p.inner_text('#npName')
        fresh = run.t('Agent')   # no name and no job until the person picks them
        run.check('an old save (“Nova”) opens, and Start fresh gives an unnamed agent for good', (before, after, now) == ('Nova', fresh, fresh), f'{before} → {after} → {now}')
    one('B-old-save', init=[SEED_LEGACY], extra=legacy)

    def skills_folder(run):   # "Add skills you already have", with a stand-in for the folder picker
        p = run.page
        run.facts['skills folder stand-in'] = p.evaluate(PICKER, 'my-skills')
        p.evaluate(SKILLS_SEED)
        p.click('#homeBtn')

        def pick():
            p.click('[data-act="skills-folder"]')
            p.wait_for_selector('[data-act="skills-write"]')
            return p.evaluate("() => [...document.querySelectorAll('dialog[open] .check')].map(c => c.textContent.replace(/\\s+/g, ' ').trim())")
        listed = pick()
        run.check('skills you already have: lists the 2 skills in the folder, and nothing else', len(listed) == 2 and 'brand-voice' in listed[0] and 'pdf-tools' in listed[1], listed)
        p.evaluate('() => { window.__confirm = window.confirm; window.confirm = () => false; }')   # say no to replacing their START-HERE.md
        p.click('[data-act="skills-write"]')
        p.wait_for_timeout(500)
        run.check('…asks before replacing a START-HERE.md it didn’t write, and keeps it when told no', p.evaluate(READ_START) == '# Someone else’s notes')
        p.evaluate('() => { window.confirm = window.__confirm; }')
        pick()
        p.click('[data-act="skills-write"]')
        p.wait_for_function("() => /START-HERE.md is saved/.test(document.querySelector('#toast').textContent)")
        start, copied = p.evaluate(READ_START), p.evaluate('() => window.__copied.at(-1) || ""')
        rows = [line for line in start.split('\n') if line.startswith('| ') and line.endswith('/SKILL.md |')]
        run.check('…writes START-HERE.md listing both, and copies the sentence for the AI', len(rows) == 2 and 'Ask for my OK' in start and '“my-skills”' in copied, f'{len(rows)} rows; {copied[:90]}')
        skill = p.evaluate("async () => (await (await (await window.__teamDir.getDirectoryHandle('pdf-tools')).getFileHandle('SKILL.md')).getFile()).text()")
        run.check('…leaves the skills untouched, and a skill’s own text never runs as code', skill.startswith('---\nname: pdf-tools') and p.evaluate('() => window.__xss') is None and not run.errors,
                  f"{skill[:30]!r}; __xss={p.evaluate('() => window.__xss')}")
    one('B-skills-you-already-have', extra=skills_folder)

    one('B-slow-computer-still-picture', query='?still=auto', extra=still_picture)

    # On its web address Helpercraft can live on the Home Screen and open offline. localhost stands in for https;
    # the 127.0.0.1 runs elsewhere stay fully locked, like a downloaded file.
    home = urls.get('http', '').replace('127.0.0.1', 'localhost')

    def home_screen(run):
        p = run.page
        scope = p.evaluate('navigator.serviceWorker.ready.then(r => r.scope)')
        run.check('web address: the offline copy starts', scope == home.rsplit('/', 1)[0] + '/', scope)
        problems = [e['errorId'] for e in run.ctx.new_cdp_session(p).send('Page.getInstallabilityErrors')['installabilityErrors'] if e['errorId'] != 'in-incognito']
        run.check('web address: can be added to the Home Screen (its ID card and icons are accepted)', not problems, problems)
        p.reload()
        p.wait_for_selector('#panelBody h2')
        run.ctx.set_offline(True)
        try:
            p.reload()
            p.wait_for_selector('#panelBody h2', timeout=30000)
            run.check('web address: opens with the network off', True)
        finally:
            run.ctx.set_offline(False)
        other = sorted({u for u in (r.split('?')[0] for r in run.requests) if not u.endswith(('/', '/helpercraft.html', '/manifest.webmanifest', '/sw.js'))
                        and '/icons/' not in u and not u.startswith(('data:', 'blob:'))})
        run.check('web address: loads only its own Home Screen files', not other, ', '.join(other))
    if home:   # needs the test server
        one('B-home-screen', url=home, extra=home_screen)

    if home and (not only or 'B-home-screen-iphone' in only):   # the one-time tip covers the bottom, so no layout checks here
        run = Run(chrome, 'B-home-screen-iphone', 'phone-390x844', home, user_agent=IPHONE_UA)

        def tip():
            run.open()
            p = run.page
            p.wait_for_selector('.hometip')
            run.check('iPhone: the Home Screen tip shows', True, p.inner_text('.hometip')[:120])
            p.click('.hometip .btn')
            p.reload()
            p.wait_for_selector('#panelBody h2')
            p.wait_for_timeout(500)
            run.check('iPhone: the tip shows only once', p.locator('.hometip').count() == 0)
            load_checks(run)
        run.attempt(tip)
        results.append(run.result())
        run.close()
    close(chrome)

    # Chrome's automatic dark mode, the nearest thing to Samsung Internet's, which pages can't switch off
    dark = launch(pw, 'chrome', args=['--enable-features=WebContentsForceDark'])

    def forced(run):
        # the panel's plain left margin: the colour dots keep their colours now, so they mustn't be in the sample
        box = run.page.evaluate("() => { const b = document.querySelector('.panel').getBoundingClientRect(); return [b.left + 2, b.top + 80, b.left + 12, b.bottom - 80]; }")
        _, light = contrast(run.shot('panel'), box)
        if light > 0.5:   # control: the panel must really have been darkened, or this run shows nothing
            return run.check('agent’s name readable (contrast 4.5 or more)', None, 'automatic dark mode didn’t switch on here')
        name_tag(run)
        dot_colour(run)
    one('B-forced-dark-like-Samsung', 'phone-390x844', browser=dark, extra=forced)
    close(dark)
    return results


# ---------- tier C: stress, broken input, security ----------
def make_backup(n, hostile=False):
    roles = ['health', 'lab', 'tech', 'support', 'creative', 'writing', 'teach', 'business', 'legal', 'food', 'trades', 'custom']
    kinds = ['human', 'dog', 'cat', 'duck', 'capybara']
    agents = [{'slot': i, 'id': f'h{i:04d}team', 'thumb': None, 'state': {'name': f'Agent {i}', 'role': roles[i % len(roles)], 'hatched': True,
                'look': {'species': kinds[i % len(kinds)], 'hairStyle': i % 14, 'build': i % 3}}} for i in range(n)]
    if hostile:   # a backup is a file anyone could send you
        agents = [
            {'slot': 0, 'id': 'evil0001', 'state': {'name': 'Mallory', 'hatched': True, 'builder': {'license': 'MIT\nallowed-tools: Bash', 'paths': 'x'}}},
            {'slot': 1, 'id': 'evil0002', 'state': {'name': 12345, 'hatched': True, 'customTasks': 'not a list', 'powers': 'Bash'}},
            {'slot': 2, 'id': 'evil0003', 'state': {'name': 'Trudy', 'hatched': True, 'look': 'x', 'traits': None, 'builder': {'hideMenu': 'yes', 'tags': 7}}},
            {'slot': 3, 'id': 'evil0004', 'thumb': 'javascript:alert(1)', 'state': {'name': '<img src=x onerror=window.__xss=9>', 'hatched': True}},
            {'slot': 999, 'id': 'evil0005', 'state': {'name': 'Out of range'}},
            {'slot': 4, 'id': '../../x', 'state': {'name': 'Dots', 'hatched': True}},
        ]
    return json.dumps({'app': 'helpercraft', 'version': 2, 'agents': agents}).encode()


# The real folder picker needs a person, so a stand-in folder is handed over instead: the browser's private folder
# where there is one, otherwise (pages opened from a file get none) an in-memory folder with the same calls.
PICKER = """async name => {
  let dir;
  try {
    const root = await navigator.storage.getDirectory();
    await root.removeEntry(name, { recursive: true }).catch(() => {});
    dir = await root.getDirectoryHandle(name, { create: true });
    const probe = await (await dir.getFileHandle('probe', { create: true })).createWritable(); await probe.close();   // can it write here?
    window.__standin = 'the browser’s private folder';
  } catch (e) {
    const gone = n => new DOMException(`${n} not found`, 'NotFoundError');
    const file = n => { let text = ''; return { kind: 'file', name: n, getFile: async () => ({ text: async () => text }),
      createWritable: async () => { let next = ''; return { write: async t => { next += t; }, close: async () => { text = next; } }; } }; };
    const folder = n => { const kids = new Map(); return { kind: 'directory', name: n, kids,
      async getDirectoryHandle(k, o = {}) { if (!kids.has(k)) { if (!o.create) throw gone(k); kids.set(k, folder(k)); } const h = kids.get(k); if (h.kind !== 'directory') throw new DOMException(k, 'TypeMismatchError'); return h; },
      async getFileHandle(k, o = {}) { if (!kids.has(k)) { if (!o.create) throw gone(k); kids.set(k, file(k)); } const h = kids.get(k); if (h.kind !== 'file') throw new DOMException(k, 'TypeMismatchError'); return h; },
      async removeEntry(k, o = {}) { const h = kids.get(k); if (!h) throw gone(k); if (h.kind === 'directory' && h.kids.size && !o.recursive) throw new DOMException(k, 'InvalidModificationError'); kids.delete(k); },
      async *entries() { for (const e of [...kids]) yield e; } }; };
    dir = folder(name);
    window.__standin = 'an in-memory folder';
  }
  const w = await (await dir.getFileHandle('helpercraft.html', { create: true })).createWritable(); await w.write('stand-in'); await w.close();
  window.__teamDir = dir;
  window.showDirectoryPicker = async () => dir;
  return window.__standin;
}"""
COUNT_TEAM = """async () => {
  const dir = window.__teamDir, agents = await dir.getDirectoryHandle('agents'); let folders = 0, skills = 0;
  for await (const [, h] of agents.entries()) { if (h.kind !== 'directory') continue; folders++; try { await h.getFileHandle('SKILL.md'); skills++; } catch (e) {} }
  const start = await (await (await dir.getFileHandle('START-HERE.md')).getFile()).text();
  return { folders, skills, rows: start.split('\\n').filter(l => /^\\| .* \\| agents\\//.test(l)).length };
}"""
TEAM_FILES = """async () => {
  const agents = await window.__teamDir.getDirectoryHandle('agents'), out = {};
  for await (const [n, h] of agents.entries()) if (h.kind === 'directory') try { out[n] = await (await (await h.getFileHandle('SKILL.md')).getFile()).text(); } catch (e) {}
  return out;
}"""
# skills made elsewhere, in the stand-in folder: two skills (one with code in its description), a folder that isn't a
# skill, and a START-HERE.md someone else wrote
SKILLS_SEED = """async () => {
  const d = window.__teamDir;
  const put = async (path, text) => { let x = d; const parts = path.split('/');
    for (const p of parts.slice(0, -1)) x = await x.getDirectoryHandle(p, { create: true });
    const w = await (await x.getFileHandle(parts.at(-1), { create: true })).createWritable(); await w.write(text); await w.close(); };
  await put('pdf-tools/SKILL.md', '---\\nname: pdf-tools\\ndescription: Extract text and tables from PDFs. Use when the user has a PDF.\\n---\\n# PDF tools\\n');
  await put('brand-voice/SKILL.md', '---\\nname: brand-voice\\ndescription: "<img src=x onerror=window.__xss=7> Write in our brand voice."\\n---\\n');
  await put('notes/todo.txt', 'not a skill');
  await put('START-HERE.md', '# Someone else’s notes');
}"""
READ_START = "async () => (await (await window.__teamDir.getFileHandle('START-HERE.md')).getFile()).text()"
USED = "() => Object.keys(localStorage).reduce((s, k) => s + k.length + localStorage.getItem(k).length, 0)"
CONNECTED = "() => document.querySelector('#teamBar').dataset.connected === 'yes'"


def reopen_home(p):
    p.evaluate("() => document.querySelector('#homeDlg').open && document.querySelector('#homeDlg').close()")
    p.click('#homeBtn')


def stress(browser, env, url, load):
    run = Run(browser, env, 'laptop-1440x900', url)
    p = run.page

    def go():
        run.open()
        t = time.time()
        p.set_input_files('#restoreFile', files=[{'name': 'backup.json', 'mimeType': 'application/json', 'buffer': make_backup(180)}])
        p.wait_for_function("() => /Restored 180|out of space/.test(document.querySelector('#toast').textContent)", timeout=180000)
        run.facts['restore 180 agents and draw their portraits (s)'] = round(time.time() - t, 1)
        run.facts['storage used by 180 agents (million characters)'] = round(p.evaluate(USED) / 1e6, 2)
        thumbs = p.evaluate("() => Object.keys(localStorage).filter(k => k.startsWith('helpercraft.agent.') && JSON.parse(localStorage.getItem(k)).thumb).length")
        has3d = not p.evaluate("() => document.documentElement.classList.contains('no-webgl')")
        run.check('180 agents restored' + (', each with a portrait' if has3d else ' (no 3D here, so no portraits)'), p.inner_text('#homeCount') == '180' and (thumbs == 180 or not has3d),
                  f"{p.inner_text('#homeCount')} agents, {thumbs} portraits; {p.inner_text('#toast')}")
        reopen_home(p)
        t, full = time.time(), 0
        for r in range(20):
            full += p.evaluate("() => document.querySelectorAll('#room .slot:not(.empty)').length") == 9
            if r < 19:
                p.click('#roomNext')
        run.facts['flip through all 20 rooms (s)'] = round(time.time() - t, 1)
        run.check('all 20 rooms show 9 agents', full == 20, f'{full} full rooms')
        p.wait_for_timeout(800)   # the room slides in
        run.shot('room-20')
        with p.expect_download() as d:
            p.click('#backupBtn')
        bk = save(d.value, run, 'backup')
        run.facts['backup file for 180 agents (MB)'] = round(bk.stat().st_size / 1e6, 2)
        run.check('backup holds all 180', len(json.loads(bk.read_text(encoding='utf-8'))['agents']) == 180)
        # the zip, for browsers that can't save into a folder
        p.evaluate('() => { window.showDirectoryPicker = undefined; }')
        reopen_home(p)
        with p.expect_download() as d:
            p.click('[data-act="team-zip"]')
        with zipfile.ZipFile(save(d.value, run, 'team')) as z:
            names = z.namelist()
            skills = [n for n in names if n.endswith('/SKILL.md')]
            bad = [n for n in skills if skill_problems(z.read(n).decode('utf-8'), CORE_KEYS | EXTRA_KEYS)]
            start = z.read('helpercraft-team/START-HERE.md').decode('utf-8') if 'helpercraft-team/START-HERE.md' in names else ''
        run.check('team zip: 180 valid agents, all listed in START-HERE.md', len(skills) == 180 and not bad and start.count('| agents/') == 180,
                  f'{len(skills)} skills, {len(bad)} invalid, {start.count("| agents/")} listed')
        # the team folder
        run.facts['team folder stand-in'] = p.evaluate(PICKER, 'stress-team')
        reopen_home(p)
        t = time.time()
        p.click('[data-act="team-folder"]')
        p.wait_for_function(CONNECTED, timeout=180000)
        run.facts['save the team folder, 180 agents (s)'] = round(time.time() - t, 1)
        team = p.evaluate(COUNT_TEAM)
        run.check('team folder: 180 agent folders, all listed in START-HERE.md', team == {'folders': 180, 'skills': 180, 'rows': 180}, team)
        p.click('[data-act="team-copy"]')
        copied = p.evaluate('() => window.__copied.at(-1) || ""')
        if load == 'file':
            run.check('Copy for my AI gives the folder’s full address', str(ROOT) in copied, 'the copied sentence names a different place')
        else:
            run.check('Copy for my AI names the folder', '“stress-team”' in copied, copied)
        load_checks(run)
    run.attempt(go)
    run.close()
    return run.result()


def storage_full(browser, env, url):
    run = Run(browser, env, 'laptop-1440x900', url)
    p = run.page

    def go():
        run.open()
        p.evaluate("() => { let i = 0; for (let n = 1 << 21; n >= 256; n >>= 1) { try { for (;;) localStorage.setItem('fill' + i++, 'x'.repeat(n)); } catch (e) {} } }")
        run.facts['browser storage limit (million characters)'] = round(p.evaluate(USED) / 1e6, 2)
        p.fill('#panelBody .name-input', 'Juniper')
        p.click('.step-tab >> nth=5')
        p.click('#panelFoot [data-act="hatch"]')
        p.wait_for_selector('.cert h2')
        toast = p.inner_text('#toast')
        run.check('storage full: says so, no crash, the agent stays on screen', 'out of space' in toast and p.inner_text('#npName') == 'Juniper' and not run.errors, toast)
        load_checks(run)
    run.attempt(go)
    run.close()
    return run.result()


# Text a person could type or paste, with characters that trip up YAML and JSON in different ways
NASTY = ['\u007f', '\u0080', '\u0085', '\u009f', '\u0000', '\u0008', '﻿', ' ', ' ', '😀', '👩🏽‍⚕️', '---', ': #', '"', "'",
         '\\', '@', '*', '&', '!', '%', '|', '>', '<', '{', '}', '[', ']', '\t', '\n', '\r\n', '​', '‮', 'é', '中文', 'ا', ' ', '#', '- ', '? ', '...']
FUZZ_JS = """([from, cases, nasty, langs]) => {
  let seed = 7 + from;
  const rng = () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  const pick = a => a[Math.floor(rng() * a.length)], some = a => a.filter(() => rng() < 0.4);
  const text = max => { let s = rng() < 0.2 ? pick(['@', '*', '&', '!', '%', '- ', '? ', '"']) : ''; const n = Math.floor(rng() * max);
    for (let i = 0; i < n; i++) s += rng() < 0.45 ? pick(nasty) : String.fromCharCode(97 + Math.floor(rng() * 26)); return s; };
  const S = Helpercraft.state, keep = JSON.parse(JSON.stringify(S)), keepLang = Helpercraft.lang, out = [];
  for (let i = 0; i < cases; i++) {
    Helpercraft.setLang(pick(langs));
    Object.assign(S, JSON.parse(JSON.stringify(keep)), {
      name: text(40), customTitle: rng() < 0.6 ? text(60) : '', workplace: text(300), catchphrase: text(80), maker: text(80),
      customTasks: [text(60), text(60)].filter(Boolean), customRules: [text(80)].filter(Boolean), customHandoff: [text(80)].filter(Boolean),
      descOverride: rng() < 0.25 ? text(200) : '', role: pick(['health', 'lab', 'tech', 'support', 'creative', 'writing', 'teach', 'business', 'legal', 'food', 'trades', 'custom', null]),
      specialty: '', invoke: pick(['auto', 'manual']), powers: some(['read', 'web', 'edit', 'run']), needs: some(['internet', 'code', 'files']),
      share: pick(['private', 'mit', 'nc', 'free']), habits: some(['clarify', 'plan', 'steps', 'check', 'next', 'first', 'bullets', 'tables', 'flow', 'plain', 'examples', 'sources']),
      builder: { license: pick(['', 'MIT', 'Apache-2.0', 'Proprietary']), compat: text(200), version: text(20), tags: text(80), paths: text(80), whenToUse: text(200), argHint: text(60), hideMenu: rng() < 0.5 },
    });
    S.look = { ...S.look, species: pick(['human', 'dog', 'cat', 'duck', 'capybara']) };
    try {
      const full = Helpercraft.buildSkill(), core = Helpercraft.buildSkill({ core: true });
      out.push({ full: full.text, files: full.files, core: core.text });
    } catch (e) { out.push({ error: String(e) }); }
  }
  Object.assign(S, keep); Helpercraft.setLang(keepLang);
  return out;
}"""


def fuzz(browser, env, url, cases):
    run = Run(browser, env, 'laptop-1440x900', url)

    def go():
        run.open()
        found, broken = {}, 0
        for start in range(0, cases, 100):
            for c in run.page.evaluate(FUZZ_JS, [start, min(100, cases - start), NASTY, ['en', 'zh', 'es']]):
                if 'error' in c:
                    probs = [f'crashed: {c["error"]}']
                else:
                    probs = skill_problems(c['full'], CORE_KEYS | EXTRA_KEYS) + skill_problems(c['core'], CORE_KEYS)
                    for path, t in c['files']:
                        try:
                            probs += roundtrip(t, yaml.safe_load(t))
                        except Exception as e:
                            probs.append(f'{path} YAML error: {str(e).splitlines()[0]}')
                broken += bool(probs)
                for pr in probs:
                    kind = re.sub(r"'.*|\(.*|\d+|YAML reads .*", '', pr).strip()
                    found.setdefault(kind, {'count': 0, 'example': pr[:160]})['count'] += 1
        run.facts['random agents checked (English, Chinese, Spanish)'] = cases
        run.facts['agents whose file was broken'] = broken
        run.check(f'{cases} random agents with tricky text, in 3 languages, all make valid files', broken == 0, json.dumps(found, ensure_ascii=True)[:1500])
        load_checks(run)
    run.attempt(go)
    run.close()
    return run.result()


def security(browser, env, url):
    run = Run(browser, env, 'laptop-1440x900', url)
    p = run.page

    def go():
        run.open()
        p.fill('#panelBody .name-input', '<img src=x onerror="window.__xss=1">')
        p.click('.step-tab >> nth=1')
        p.fill('#panelBody input[placeholder="Or type your own job title"]', '"><svg onload="window.__xss=2">')
        p.fill('#panelBody input[placeholder^="Add a task"]', '<script>window.__xss=3</script>')
        p.press('#panelBody input[placeholder^="Add a task"]', 'Enter')
        p.fill('#panelBody textarea', '<iframe src="javascript:window.__xss=4">')
        p.click('.step-tab >> nth=2')
        p.fill('#panelBody input[placeholder^="e.g. Let"]', '<b onmouseover="window.__xss=5">hi</b>')
        p.click('.step-tab >> nth=5')
        p.fill('#panelBody input[placeholder="e.g. Sam Rivera"]', '<img src=x onerror=window.__xss=6>')
        p.click('#panelFoot [data-act="hatch"]')
        p.wait_for_selector('.cert h2')
        p.click('#dockToggle')
        p.click('[data-act="peek"]')
        p.evaluate("() => document.querySelector('#fileDlg').close()")
        run.facts['team folder stand-in'] = p.evaluate(PICKER, 'xss-team')
        reopen_home(p)
        p.click('#room .slot:not(.empty)')
        p.click('[data-act="team-folder"]')
        p.wait_for_function(CONNECTED, timeout=60000)
        p.wait_for_timeout(1000)
        fired = p.evaluate('() => window.__xss')
        run.check('code typed into the text boxes never runs (name, job, task, workplace, catchphrase, maker)', fired is None and not run.dialogs, f'__xss={fired}, dialogs={run.dialogs}')
        run.check('…it shows as plain text', p.inner_text('#npName').startswith('<img'), p.inner_text('#npName'))
        before = len(run.console)
        verdict = p.evaluate("""async () => ({
          fetch: await fetch('https://example.com/').then(() => 'loaded', () => 'blocked'),
          image: await new Promise(r => { const i = new Image(); i.onload = () => r('loaded'); i.onerror = () => r('blocked'); i.src = 'https://example.com/x.png'; }) })""")
        run.check('the privacy lock blocks the internet (fetch and images)', verdict == {'fetch': 'blocked', 'image': 'blocked'}, verdict)
        del run.console[before:]   # the browser's notes about the blocked tries above aren't the page's errors
        unnamed = p.evaluate("() => [...document.querySelectorAll('button')].filter(b => b.getClientRects().length && !(b.textContent.trim() || b.getAttribute('aria-label'))).map(b => b.outerHTML.slice(0, 80))")
        run.check('every visible button has a name (screen readers)', not unnamed, unnamed)
        p.keyboard.press('Escape')
        try:   # WebKit closes the dialog a moment later, not at once
            p.wait_for_function("() => !document.querySelector('#homeDlg').open", timeout=3000)
        except Exception:
            pass
        run.check('Escape closes Agent home', not p.evaluate("() => document.querySelector('#homeDlg').open"))
        # a backup is a file anyone could send: wrong types, extra settings smuggled into the file, bad pictures
        p.set_input_files('#restoreFile', files=[{'name': 'backup.json', 'mimeType': 'application/json', 'buffer': make_backup(0, hostile=True)}])
        p.wait_for_function("() => /Restored|isn’t a Helpercraft/.test(document.querySelector('#toast').textContent)")
        for _ in range(40):   # the connected team folder updates in the background
            files = p.evaluate(TEAM_FILES)
            if len(files) == 5:
                break
            p.wait_for_timeout(250)
        smuggled = [n for n, t in files.items() if 'allowed-tools' in frontmatter(t) or skill_problems(t, CORE_KEYS | EXTRA_KEYS)]
        run.check('a tampered backup can’t add settings to an agent’s file (like allowed-tools)', len(files) == 5 and not smuggled, smuggled or f'{len(files)} agent files')
        reopen_home(p)
        shown = p.evaluate("() => document.querySelectorAll('#room .slot:not(.empty)').length")
        run.check('a tampered backup doesn’t break Agent home, the team folder, or run code', shown == 5 and p.evaluate(CONNECTED)
                  and not run.errors and p.evaluate('() => window.__xss') is None, f'{shown} agents shown; ' + '; '.join(run.errors)[:400])
        run.console[:] = [c for c in run.console if 'example.com' not in c]   # Firefox reports the blocked tries above a little later
        load_checks(run)
    run.attempt(go)
    run.close()
    return run.result()


def two_tabs(browser, env, url):
    run = Run(browser, env, 'laptop-1440x900', url)

    def go():
        run.open()
        second = run.ctx.new_page()
        second.goto(url)
        second.wait_for_selector('#panelBody h2')
        for page, name in ((run.page, 'Ivy'), (second, 'Moss')):
            page.fill('#panelBody .name-input', name)
            page.click('.step-tab >> nth=5')
            page.click('#panelFoot [data-act="hatch"]')
            page.wait_for_selector('.cert h2')
        run.page.reload()
        run.page.wait_for_selector('#panelBody h2')
        names = run.page.evaluate("() => Object.keys(localStorage).filter(k => k.startsWith('helpercraft.agent.')).map(k => JSON.parse(localStorage.getItem(k)).state.name).sort()")
        run.check('two tabs open at once: both agents kept in Agent home', names == ['Ivy', 'Moss'], names)
        load_checks(run)
    run.attempt(go)
    run.close()
    return run.result()


def tier_c(pw, urls):
    results = []
    for eng, load in (('chrome', 'file'), ('edge', 'http'), ('firefox', 'http'), ('webkit', 'http')):
        browser = launch(pw, eng)
        results.append(stress(browser, f'C-{eng}-{load}-stress', urls[load], load))
        results.append(two_tabs(browser, f'C-{eng}-{load}-two-tabs', urls[load]))
        results.append(storage_full(browser, f'C-{eng}-{load}-storage-full', urls[load]))
        if eng in ('chrome', 'edge'):
            results.append(fuzz(browser, f'C-{eng}-{load}-fuzz', urls[load], 1000 if eng == 'chrome' else 300))
        results.append(security(browser, f'C-{eng}-{load}-security', urls[load]))
        close(browser)
    return results


# ---------- running and reporting ----------
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def serve():
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}/helpercraft.html'


def git(*args):
    try:
        return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True).stdout.strip()
    except OSError:
        return '?'


def summary(meta, runs):
    mark = {True: '✅', False: '❌', None: '➖'}
    lines = [f"# Test run {meta['date']}", '', f"Commit {meta['commit']}{' (with local changes)' if meta['dirty'] else ''} · {meta['os']} · "
             + ', '.join(f'{k} {v}' for k, v in meta['browsers'].items()) + f" · {meta['minutes']} min", '',
             '| Environment | Screen | Passed | Failed | Facts |', '|---|---|---|---|---|']
    for r in runs:
        good = sum(c['ok'] is True for c in r['checks'])
        bad = [c['check'] for c in r['checks'] if c['ok'] is False]
        facts = '; '.join(f'{k}: {v}' for k, v in r['facts'].items())
        lines.append(f"| {r['env']} | {r['device']} | {good} | {', '.join(bad) or '0'} | {facts} |")
    lines += ['', '## Every check', '']
    for r in runs:
        lines.append(f"**{r['env']} · {r['device']}**")
        lines += [f"- {mark[c['ok']]} {c['check']}" + (f" — {c['detail'][:300]}" if c['ok'] is not True and c['detail'] else '') for c in r['checks']]
        lines.append('')
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tiers', default='ALBC')
    ap.add_argument('--rounds', type=int, default=2)
    ap.add_argument('--engines', default='chromium,chrome,edge,firefox,webkit')
    args = ap.parse_args()
    for d in ('shots', 'downloads'):
        (OUT / d).mkdir(parents=True, exist_ok=True)
    srv, http_url = serve()
    urls = {'file': PAGE.as_uri(), 'http': http_url}
    versions = {}
    PROGRESS['meta'] = meta = {'date': datetime.datetime.now().isoformat(timespec='minutes'), 'start': time.time(), 'commit': git('rev-parse', '--short', 'HEAD'),
                               'dirty': bool(git('status', '--porcelain', '--', 'helpercraft.html')), 'os': f'{platform.system()} {platform.release()} (build {platform.version()})',
                               'python': platform.python_version(), 'browsers': versions, 'tiers': args.tiers}
    with sync_playwright() as pw:
        for eng in ENGINES:
            try:
                b = launch(pw, eng)
                versions[eng] = b.version
                close(b)
            except Exception as e:
                versions[eng] = f'not available ({str(e).splitlines()[0][:60]})'
        tiers = [('A', 'Tier A: the whole flow everywhere', lambda: tier_a(pw, urls, args.rounds, args.engines.split(','))),
                 ('L', 'Tier L: Chinese and Spanish', lambda: tier_l(pw, urls)),
                 ('B', 'Tier B: one setting at a time', lambda: tier_b(pw, urls)),
                 ('C', 'Tier C: stress, broken input, security', lambda: tier_c(pw, urls))]
        for key, title, fn in tiers:
            if key in args.tiers:
                print(title, flush=True)
                fn()
        save_progress()
        runs = PROGRESS['runs']
        (OUT / 'summary.md').write_text(summary(meta, runs), encoding='utf-8')   # all written before Playwright shuts down, in case that hangs
        failed = [(r['env'], r['device'], c) for r in runs for c in r['checks'] if c['ok'] is False]
        print(f"\n{sum(c['ok'] is True for r in runs for c in r['checks'])} passed, {len(failed)} failed, in {meta['minutes']} min", flush=True)
        for env, dev, c in failed:
            print(f"  FAIL {env} {dev}: {c['check']} — {c['detail'][:300]}", flush=True)
    srv.shutdown()
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
