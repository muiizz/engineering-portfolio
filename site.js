/* Interactive evidence for the portfolio. Every number here is copied from a
   file in the linked repositories; the comment above each block names it. */
(() => {
  'use strict';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const el = (tag, attrs = {}, ...kids) => {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === 'class') n.className = v;
      else if (k === 'text') n.textContent = v;
      else if (k.startsWith('on')) n.addEventListener(k.slice(2), v);
      else n.setAttribute(k, v);
    }
    for (const k of kids) n.append(k);
    return n;
  };
  const seg = (label, options, value, onPick) => {
    const box = el('div', { class: 'seg', role: 'group', 'aria-label': label });
    const set = (v) => {
      value = v;
      [...box.children].forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.v === String(v))));
    };
    options.forEach(([v, text, aria]) => {
      const b = el('button', { type: 'button', 'data-v': v, text, onclick: () => { set(v); onPick(v); } });
      if (aria) b.setAttribute('aria-label', aria);
      box.append(b);
    });
    set(value);
    box.set = set;
    return box;
  };
  const edge = (a, b) => el('div', { class: 'edge' }, el('span', { text: a }), el('span', { text: b }));

  /* ---------- Kinetic headline: letter width follows the pointer ---------- */
  document.querySelectorAll('.kin').forEach((h) => {
    const text = h.textContent.trim();
    h.setAttribute('aria-label', text);
    const lines = h.innerHTML.split(/<br\s*\/?>/i);
    h.textContent = '';
    let i = 0;
    const chars = [];
    lines.forEach((line, li) => {
      const tmp = el('span'); tmp.innerHTML = line;
      tmp.textContent.trim().split(/\s+/).forEach((word, wi, arr) => {
        const w = el('span', { class: 'w', 'aria-hidden': 'true' });
        [...word].forEach((ch) => {
          const c = el('span', { class: 'c', text: ch });
          c.style.setProperty('--i', i++);
          chars.push(c); w.append(c);
        });
        h.append(w);
        if (wi < arr.length - 1) h.append(' ');
      });
      if (li < lines.length - 1) h.append(el('br'));
    });
    if (reduce) return;
    h.classList.add('pre', 'settle');
    requestAnimationFrame(() => requestAnimationFrame(() => h.classList.remove('pre')));
    setTimeout(() => h.classList.remove('settle'), 1000 + chars.length * 22);
    if (!matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    let boxes = [], raf = 0, px = -1e4, py = -1e4;
    const measure = () => { boxes = chars.map((c) => { const r = c.getBoundingClientRect(); return [r.left + r.width / 2 + scrollX, r.top + r.height / 2 + scrollY]; }); };
    const paint = () => {
      raf = 0;
      const R = Math.max(160, innerWidth * 0.2);
      chars.forEach((c, k) => {
        const d = Math.hypot(boxes[k][0] - px, boxes[k][1] - py);
        const t = Math.max(0, 1 - d / R);
        const e = t * t * (3 - 2 * t);
        c.style.setProperty('--wd', (100 - 34 * e).toFixed(1));
        c.style.setProperty('--wt', Math.round(800 - 420 * e));
      });
    };
    const zone = h.closest('section') || h;
    zone.addEventListener('pointerenter', measure);
    zone.addEventListener('pointermove', (ev) => { if (!boxes.length) measure(); px = ev.pageX; py = ev.pageY; raf = raf || requestAnimationFrame(paint); });
    zone.addEventListener('pointerleave', () => { px = py = -1e4; h.classList.add('settle'); paint(); setTimeout(() => h.classList.remove('settle'), 900); });
    addEventListener('resize', () => { boxes = []; });
  });

  /* ---------- Takes: llm-safety-rules-engine, python/evals/results/R0..R3.json
     and mutation-R0..R3.json, test split (90 urgent, 81 routine) ---------- */
  const ROUNDS = [
    { id: 'R0', change: 'English-only lexicon.', mut: [112, 115],
      en: [9, 21, 4, 23], ru: [0, 30, 0, 27], ur: [0, 30, 0, 27] },
    { id: 'R1', change: 'Roman Urdu and Urdu script phrases added, as direct translations of the English rules.', mut: [112, 115],
      en: [9, 21, 4, 23], ru: [13, 17, 1, 26], ur: [10, 20, 1, 26] },
    { id: 'R2', change: 'Spellings folded: repeated Latin letters, common Roman Urdu variants, Arabic letter forms, vowel marks, invisible joiners.', mut: [164, 169],
      en: [9, 21, 6, 21], ru: [24, 6, 3, 24], ur: [24, 6, 3, 24] },
    { id: 'R3', change: 'Proximity rules added (a symptom word and a trouble word within a few words), plus convulsion terms.', mut: [189, 196],
      en: [27, 3, 6, 21], ru: [30, 0, 3, 24], ur: [30, 0, 3, 24] },
  ];
  const LANGS = [['en', 'English'], ['ru', 'Roman Urdu'], ['ur', 'Urdu script']];
  function takes(root, full) {
    root.textContent = '';
    let at = 0, timer = 0;
    const missed = el('div', { class: 'big is-red' });
    const falses = el('div', { class: 'big is-wax' });
    const mut = el('div', { class: 'big' });
    const change = el('p', { class: 'change', 'aria-live': 'polite' });
    const langs = el('div', { class: 'langs' });
    const cols = LANGS.map(([key, name]) => {
      const count = el('span');
      const u = el('div', { class: 'dots', role: 'img' });
      const r = el('div', { class: 'dots r', role: 'img' });
      for (let i = 0; i < 30; i++) { const d = el('i'); d.style.setProperty('--n', i); u.append(d); }
      for (let i = 0; i < 27; i++) { const d = el('i'); d.style.setProperty('--n', i + 30); r.append(d); }
      langs.append(el('div', { class: 'lang' }, el('h4', {}, el('span', { text: name }), count), u, r));
      return { key, name, count, u, r };
    });
    const show = (i) => {
      at = i; const R = ROUNDS[i];
      const tot = LANGS.reduce((s, [k]) => [s[0] + R[k][1], s[1] + R[k][2]], [0, 0]);
      missed.replaceChildren(`${tot[0]} of 90`, el('small', { text: 'urgent messages missed' }));
      falses.replaceChildren(`${tot[1]} of 81`, el('small', { text: 'routine messages flagged urgent' }));
      mut.replaceChildren(`${R.mut[0]} of ${R.mut[1]}`, el('small', { text: 'code mutants killed by the tests' }));
      change.textContent = `${R.id}: ${R.change}`;
      cols.forEach((c) => {
        const [tp, fn, fp] = R[c.key];
        [...c.u.children].forEach((d, n) => { d.className = n < tp ? 'found' : 'miss'; });
        [...c.r.children].forEach((d, n) => { d.className = n < fp ? 'false' : ''; });
        c.count.textContent = `${tp} of 30 found`;
        c.u.setAttribute('aria-label', `${c.name}: ${tp} of 30 urgent found, ${fn} missed`);
        c.r.setAttribute('aria-label', `${c.name}: ${fp} of 27 routine flagged urgent`);
      });
      picker.set(i);
    };
    const picker = seg('Revision', ROUNDS.map((r, i) => [i, r.id, `Revision ${r.id}`]), 0, (v) => { clearInterval(timer); show(+v); });
    const play = el('button', { type: 'button', class: 'btn ghost', text: 'Play all four', onclick: () => {
      clearInterval(timer); show(0);
      timer = setInterval(() => { if (at >= 3) return clearInterval(timer); show(at + 1); }, reduce ? 1200 : 1500);
    } });
    root.append(
      edge('Urgent routing, test split', '171 synthetic messages, 23 Nov 2026'),
      el('div', { class: 'row' }, picker, play),
      el('div', { class: 'readouts' }, missed, falses, mut),
      change, langs,
      el('div', { class: 'legend' },
        el('span', {}, el('i', { class: 'found' }), 'Urgent, found'),
        el('span', {}, el('i', { class: 'miss' }), 'Urgent, missed'),
        el('span', {}, el('i', { class: 'false' }), 'Routine, flagged urgent'),
        el('span', {}, el('i'), 'Routine, left alone')),
    );
    if (full) root.append(el('p', { class: 'note', text: 'Each mark is one fixture in the count, in count order. The results files record totals per language, so a mark does not identify a specific message.' }));
    show(0);
  }

  /* ---------- Fold: the R2 failure recorded in docs/fix_loop.md ---------- */
  function fold(root) {
    root.textContent = '';
    const PATTERN = 'no need to see a doctor';
    const input = el('textarea', { rows: '2', id: 'fold-in' });
    input.value = 'There is no need to see a doctor.';
    const out = el('div', { class: 'bins' });
    const collapse = (s) => s.toLowerCase().replace(/([a-z])\1+/g, '$1');
    const lane = (title, text, hit) => el('div', { class: 'bin on' + (hit ? '' : ' review') },
      el('h4', { text: title }),
      el('div', { class: 'slip' }, text, el('small', { text: hit ? 'Output check matches. The unsafe reply is blocked.' : 'Output check finds nothing. The unsafe reply would pass.' })));
    const run = () => {
      const plain = input.value.toLowerCase();
      const folded = collapse(input.value);
      out.replaceChildren(
        lane('One shared path (R2 as first written)', folded, folded.includes(PATTERN)),
        lane('Separate plain path (the fix)', plain, plain.includes(PATTERN)));
    };
    input.addEventListener('input', run);
    root.append(edge('What broke during iteration', 'Illustration of the recorded failure'),
      el('div', { class: 'field' }, el('label', { for: 'fold-in', text: 'A model reply the output check must stop' }), input),
      el('p', { class: 'kv' }, 'The output check looks for ', el('b', { text: `“${PATTERN}”` }), '. Folding repeated letters helps the rules match misspellings, and it also rewrites the text this check reads.'),
      out,
      el('p', { class: 'note', text: 'This uses a one-line letter fold to show the mechanism. The engine’s own normaliser and tests are in the linked repository.' }));
    run();
  }

  /* ---------- Scan: labs/postgres/measured/summary.json and the suite table
     in labs/postgres/README.md (medians of five warm runs, ms) ---------- */
  const CASES = [
    ['Tenant week', 67.169, 0.126, 96, 'Case study run'],
    ['Student history', 46.283, 0.028, 10, 'Suite'],
    ['Absence review', 49.983, 0.471, 500, 'Suite'],
    ['Date export', 55.44, 0.171, 1370, 'Suite'],
    ['Month filter', 160.394, 35.198, 42465, 'Suite'],
    ['Deep pagination', 114.436, 0.027, 100, 'Suite'],
  ];
  function scan(root, full) {
    root.textContent = '';
    const SLOW = 40, COLS = 64, ROWS = 36, N = COLS * ROWS;
    let cur = CASES[0], raf = 0, marks = [];
    const rng = (seed) => () => (seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296;
    const mk = (title) => {
      const canvas = el('canvas', { role: 'img' });
      const time = el('div', { class: 'big' });
      const box = el('div', { class: 'lane' }, el('h4', { text: title }), canvas, time);
      return { canvas, time, box, p: 0 };
    };
    const A = mk('Before: primary key only'), B = mk('After: with the added index');
    const pick = () => {
      const m = cur[3] <= 120 ? cur[3] : Math.round(120 + 100 * Math.log10(cur[3] / 120));
      const r = rng(cur[3] * 7 + 3), set = new Set();
      while (set.size < m) set.add(Math.floor(r() * N));
      marks = [...set].sort((a, b) => a - b);
    };
    const draw = (L, indexed) => {
      const c = L.canvas, dpr = Math.min(devicePixelRatio || 1, 2);
      const w = c.clientWidth, h = c.clientHeight;
      if (!w) return;
      if (c.width !== Math.round(w * dpr)) { c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); }
      const g = c.getContext('2d');
      g.setTransform(dpr, 0, 0, dpr, 0, 0);
      g.clearRect(0, 0, w, h);
      const cw = w / COLS, ch = h / ROWS, s = Math.max(1.2, Math.min(cw, ch) * 0.62);
      const front = Math.floor(L.p * N);
      for (let i = 0; i < N; i++) {
        const read = !indexed && i < front;
        g.fillStyle = read ? '#8f8473' : '#453d33';
        g.fillRect((i % COLS) * cw + (cw - s) / 2, Math.floor(i / COLS) * ch + (ch - s) / 2, s, s);
      }
      const lit = indexed ? Math.floor(L.p * marks.length) : marks.length;
      g.fillStyle = '#f5c518';
      for (let k = 0; k < marks.length; k++) {
        const i = marks[k];
        if (indexed ? k >= lit : i >= front) continue;
        g.fillRect((i % COLS) * cw + (cw - s * 1.5) / 2, Math.floor(i / COLS) * ch + (ch - s * 1.5) / 2, s * 1.5, s * 1.5);
      }
      if (!indexed && L.p > 0 && L.p < 1) {
        g.fillStyle = 'rgba(224,48,30,.9)';
        g.fillRect(0, Math.floor(front / COLS) * ch, w, Math.max(2, ch));
      }
    };
    const label = (L, ms, done, indexed) => {
      L.time.replaceChildren(`${ms.toFixed(3)} ms`, el('small', { text: done
        ? (indexed ? `${cur[3].toLocaleString('en')} matching rows returned` : `Same ${cur[3].toLocaleString('en')} rows, after reading the table`)
        : (ms > 0 && !indexed ? 'Reading the whole table' : 'Ready') }));
      L.canvas.setAttribute('aria-label', `${indexed ? 'Indexed' : 'Baseline'} query, median ${(indexed ? cur[2] : cur[1])} milliseconds`);
    };
    const reset = () => { cancelAnimationFrame(raf); A.p = B.p = 0; pick(); draw(A, false); draw(B, true); label(A, 0, false, false); label(B, 0, false, true); go.disabled = false; go.textContent = 'Run both queries'; };
    const finish = () => { A.p = B.p = 1; draw(A, false); draw(B, true); label(A, cur[1], true, false); label(B, cur[2], true, true); go.disabled = false; go.textContent = 'Run again'; };
    const go = el('button', { type: 'button', class: 'btn', text: 'Run both queries', onclick: () => {
      cancelAnimationFrame(raf); pick();
      if (reduce) return finish();
      go.disabled = true; go.textContent = 'Running';
      const t0 = performance.now();
      const tick = (now) => {
        const sim = (now - t0) / SLOW;
        A.p = Math.min(1, sim / cur[1]); B.p = Math.min(1, sim / cur[2]);
        draw(A, false); draw(B, true);
        label(A, Math.min(sim, cur[1]), A.p >= 1, false); label(B, Math.min(sim, cur[2]), B.p >= 1, true);
        if (A.p < 1 || B.p < 1) raf = requestAnimationFrame(tick); else finish();
      };
      raf = requestAnimationFrame(tick);
    } });
    root.append(edge('One million attendance rows', 'PostgreSQL 16.2, medians of five warm runs'));
    if (full) root.append(el('div', { class: 'row cases' }, seg('Query', CASES.map((c, i) => [i, c[0]]), 0, (v) => { cur = CASES[+v]; reset(); })));
    root.append(el('div', { class: 'row' }, go), el('div', { class: 'lanes' }, A.box, B.box),
      el('p', { class: 'note', text: 'Paced from the measured medians and slowed 40 times so the gap is visible. It replays recorded timings and does not run a database. Each square stands for a block of rows; yellow marks the matches.' }));
    new ResizeObserver(() => { draw(A, false); draw(B, true); }).observe(A.canvas);
    reset();
  }

  /* ---------- Gate: demo/quality_gate.py, and GATES.md in quality-template ---------- */
  const FAULTS = [
    ['fake-secret', 'Secret scan (gitleaks)', 'A key or token in the index, working tree, or Git history.'],
    ['python-lint-error', 'Python lint (ruff)', 'Unused imports, likely bugs, unsafe calls.'],
    ['python-format-error', 'Python format (ruff format)', 'Style arguments in review.'],
    ['python-type-error', 'Python types (mypy, strict)', 'Wrong types that tests do not reach.'],
    ['typescript-lint-error', 'TypeScript lint (eslint)', 'var, loose equality, unused code.'],
    ['typescript-type-aware-lint-error', 'TypeScript lint (eslint)', 'Unsafe assignments from any.'],
    ['typescript-format-error', 'TypeScript format (prettier)', 'Style arguments in review.'],
    ['typescript-type-error', 'TypeScript types (tsc, strict)', 'Type errors in code that is never run by a test.'],
    ['sql-lint-error', 'SQL lint (sqlfluff)', 'Inconsistent or unsafe SQL style.'],
    ['trailing-whitespace', 'File hygiene (pre-commit-hooks)', 'Missing final newline, trailing spaces, large files.'],
    ['python-failing-test', 'Tests (pytest)', 'Behaviour changes nobody meant.'],
    ['typescript-failing-test', 'Tests (vitest)', 'Behaviour changes nobody meant.'],
    ['python-coverage-below-threshold', 'Coverage 90% (pytest-cov)', 'New code that no test runs.'],
    ['typescript-coverage-below-threshold', 'Coverage 90% (vitest v8)', 'New code that no test runs.'],
  ];
  function gate(root, full) {
    root.textContent = '';
    const REQUIRED = ['tests', 'lint', 'security'];
    const state = { tests: 'pass', lint: 'pass', security: 'pass' };
    const out = el('div', { class: 'out', 'aria-live': 'polite' });
    const code = el('div', { class: 'cmd' });
    const term = el('div', { class: 'term' }, el('div', { class: 'cmd', text: '$ python demo/quality_gate.py' }), out, code);
    const bar = el('div', { class: 'barrier', 'aria-hidden': 'true' }, el('i'));
    const render = (jolt) => {
      // Same rule as check_release(): each required check must be present and exactly "pass".
      const issues = [];
      for (const c of REQUIRED) {
        if (state[c] === 'missing') issues.push(`${c}: missing`);
        else if (state[c] !== 'pass') issues.push(`${c}: ${state[c]}`);
      }
      out.textContent = issues.length ? 'Release blocked: ' + issues.join(', ') : 'Release gate passed';
      code.textContent = `exit code ${issues.length ? 1 : 0}`;
      term.className = 'term ' + (issues.length ? 'block' : 'pass');
      bar.classList.toggle('open', !issues.length);
      if (jolt && issues.length && !reduce) { bar.classList.remove('jolt'); void bar.offsetWidth; bar.classList.add('jolt'); }
    };
    const checks = el('div', { class: 'checks' });
    REQUIRED.forEach((c) => checks.append(el('div', { class: 'check' }, el('strong', { text: c }),
      seg(`Result for ${c}`, [['pass', 'pass'], ['fail', 'fail'], ['missing', 'never ran']], 'pass', (v) => { state[c] = v; render(true); }))));
    root.append(edge('Release policy', 'Three required checks'), checks, bar, term);
    if (!full) root.append(el('p', { class: 'note', text: 'Set a check to fail, or remove it. The verdict uses the same rule as the Python source.' }));
    render(false);
  }
  function proofs(root) {
    root.textContent = '';
    const verdict = el('div', { class: 'verdict', 'aria-live': 'polite' });
    const chips = el('div', { class: 'faults' });
    const pick = (i, b) => {
      [...chips.children].forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
      if (i < 0) verdict.replaceChildren(el('strong', { text: 'Clean copy: every gate passes' }), 'The control. An untouched copy of the repository must pass, so a block means the fault caused it.');
      else verdict.replaceChildren(el('strong', { class: 'is-red', text: `Blocked by ${FAULTS[i][1]}` }), `The mistake this gate stops: ${FAULTS[i][2]}`);
    };
    FAULTS.forEach((f, i) => { const b = el('button', { type: 'button', class: 'chip bad', text: f[0], onclick: () => pick(i, b) }); chips.append(b); });
    const clean = el('button', { type: 'button', class: 'chip', text: 'clean copy', onclick: () => pick(-1, clean) });
    chips.append(clean);
    root.append(edge('Fault proofs in quality-template', '14 injected faults, 1 clean control'),
      el('p', { class: 'kv', text: 'Each proof injects one fault into a disposable copy of the repository and checks that the expected gate fails. Pick a fault to see what stops it.' }),
      chips, verdict,
      el('p', { class: 'note', text: 'Gate names and descriptions are from GATES.md. Two further proofs test the adoption script, and a separate run proves the mutation gate catches weak tests.' }));
    pick(0, chips.firstChild);
  }

  /* ---------- Router: a port of labs/routing-audit/routing.py ---------- */
  const BASE = ['account hacked', 'unauthorized charge', 'charged twice'];
  const REVISED = BASE.concat(['account hack ho gaya', 'do baar paisay kat gaye', 'meri ijazat ke baghair payment', 'اکاؤنٹ ہیک', 'دو بار پیسے کٹ گئے', 'بلا اجازت ادائیگی']);
  const rule = (list) => new RegExp('(?<![\\p{L}\\p{N}_])(?:' + list.map((s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')(?![\\p{L}\\p{N}_])', 'u');
  const BASE_RULE = rule(BASE), REVISED_RULE = rule(REVISED);
  const VARIANTS = { 'ي': 'ی', 'ك': 'ک', 'ـ': '', '‌': '', '‍': '' };
  const normalize = (m) => (m.normalize('NFKC').toLowerCase().replace(/[يكـ‌‍]/g, (c) => VARIANTS[c]).replace(/\p{Mn}/gu, '').match(/[\p{L}\p{N}]+/gu) || []).join(' ');
  const route = (message, consent, revised) => {
    const text = revised ? normalize(message) : message.toLowerCase();
    const m = (revised ? REVISED_RULE : BASE_RULE).exec(text);
    const queue = m ? 'review' : 'routine';
    return { queue, share: queue === 'review' && consent === true, text, match: m };
  };
  const FIXTURES = [
    ['en01', 'English', 'My account was accessed by someone else. Account hacked.', 'review'],
    ['en02', 'English', 'I see an unauthorized charge on my statement.', 'review'],
    ['en03', 'English', 'I was charged twice for one order.', 'review'],
    ['en04', 'English', 'An unknown device signed in and changed my password.', 'review'],
    ['en05', 'English', 'Where is the receipt for my order?', 'routine'],
    ['en06', 'English', 'How do I change the shipping address?', 'routine'],
    ['ru01', 'Roman Urdu', 'Mera account hack ho gaya, madad chahiye.', 'review'],
    ['ru02', 'Roman Urdu', 'Ek order ke do baar paisay kat gaye.', 'review'],
    ['ru03', 'Roman Urdu', 'Meri ijazat ke baghair payment hui.', 'review'],
    ['ru04', 'Roman Urdu', 'Order ki receipt kahan milay gi?', 'routine'],
    ['ru05', 'Roman Urdu', 'Mera account hack ho gaya tha? Nahi, sirf sign-in ka tareeqa pooch raha hoon.', 'routine'],
    ['ru06', 'Roman Urdu', 'Kya delivery kal ho sakti hai?', 'routine'],
    ['ur01', 'Urdu', 'میرا اکاؤنٹ ہیک ہو گیا ہے۔', 'review'],
    ['ur02', 'Urdu', 'ایک آرڈر کے دو بار پيسے كٹ گئے۔', 'review'],
    ['ur03', 'Urdu', 'میرے کارڈ سے بلا اجازت ادائیگی ہوئی۔', 'review'],
    ['ur04', 'Urdu', 'مجھے اپنی رسید چاہیے۔', 'routine'],
    ['ur05', 'Urdu', 'میرا پارسل کب پہنچے گا؟', 'routine'],
    ['ur06', 'Urdu', 'مجھے اپنا پتہ تبدیل کرنا ہے۔', 'routine'],
  ];
  function router(root) {
    root.textContent = '';
    let revised = true, expected = null;
    const input = el('textarea', { rows: '2', id: 'route-in', dir: 'auto' });
    const consent = el('input', { type: 'checkbox', id: 'route-consent' });
    const review = el('div', { class: 'bin review' }, el('h4', { text: 'Review queue' }));
    const routine = el('div', { class: 'bin' }, el('h4', { text: 'Routine queue' }));
    const meta = el('p', { class: 'kv', 'aria-live': 'polite' });
    const tally = el('div', { class: 'tally' });
    const chips = el('div', { class: 'faults' });
    const count = () => {
      let tp = 0, fp = 0, fn = 0;
      FIXTURES.forEach((f, i) => {
        const got = route(f[2], false, revised).queue;
        if (f[3] === 'review' && got === 'review') tp++;
        if (f[3] === 'routine' && got === 'review') fp++;
        if (f[3] === 'review' && got === 'routine') fn++;
        chips.children[i].classList.toggle('bad', got !== f[3]);
      });
      tally.replaceChildren(
        el('div', { class: 'big' }, `${tp} of 10`, el('small', { text: 'review-worthy messages reached review' })),
        el('div', { class: 'big is-red' }, String(fn), el('small', { text: 'missed' })),
        el('div', { class: 'big is-wax' }, String(fp), el('small', { text: 'unnecessary reviews' })));
    };
    const run = () => {
      const msg = input.value.trim();
      [review, routine].forEach((b) => { b.classList.remove('on'); b.querySelector('.slip')?.remove(); });
      if (!msg) { meta.textContent = 'Type a message or pick one of the 18 fixtures.'; return; }
      const d = route(msg, consent.checked, revised);
      const slip = el('div', { class: 'slip', dir: 'auto' });
      if (d.match) slip.append(d.text.slice(0, d.match.index), el('mark', { text: d.match[0] }), d.text.slice(d.match.index + d.match[0].length));
      else slip.append(d.text || msg);
      slip.append(el('small', { text: d.match ? 'Matched a review phrase' : 'No review phrase matched' }));
      const bin = d.queue === 'review' ? review : routine;
      bin.classList.add('on'); bin.append(slip);
      const verdict = expected && expected.msg === msg ? (expected.want === d.queue ? ' The fixture label agrees.' : ` The fixture is labelled ${expected.want}, so this is an error.`) : '';
      meta.replaceChildren('Transcript shared with the reviewer: ', el('b', { text: d.share ? 'yes' : 'no' }),
        d.queue === 'review' && !d.share ? ' (no explicit consent).' : '.', verdict);
    };
    FIXTURES.forEach((f) => {
      const b = el('button', { type: 'button', class: 'chip', text: f[0], title: f[2], 'aria-label': `Fixture ${f[0]}, ${f[1]}`, onclick: () => {
        [...chips.children].forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
        input.value = f[2]; expected = { msg: f[2], want: f[3] }; run();
      } });
      chips.append(b);
    });
    input.addEventListener('input', run);
    consent.addEventListener('change', run);
    root.append(edge('Support routing, 18 fictional messages', 'Runs the repository rules in your browser'),
      el('div', { class: 'row' }, seg('Policy', [[0, 'Baseline: 3 English phrases'], [1, 'Revised: 9 phrases, normalised']], 1, (v) => { revised = !!+v; count(); run(); })),
      tally,
      el('div', { class: 'field' }, el('label', { for: 'route-in', text: 'Message' }), input),
      chips,
      el('label', { class: 'toggle', for: 'route-consent' }, consent, 'Customer gave explicit consent to share the transcript'),
      el('div', { class: 'bins' }, review, routine), meta,
      el('p', { class: 'note', text: 'Fixtures underlined in red are the ones the selected policy gets wrong. Try ru05, which states a matching phrase and then rules it out, and en04, which neither policy catches.' }));
    count(); chips.children[6].click();
  }

  /* ---------- Grader: demo/eval.py and demo/cases.json ---------- */
  const GRADES = {
    refund: { name: 'Refund approval', prompt: 'I need a refund approved by a person.', route: 'handoff', phrase: 'support team', sample: 'I am passing this to our support team for approval.' },
    hours: { name: 'Desk hours', prompt: 'When is the fictional support desk open? Its published hours are 9 to 5 UTC.', route: 'reply', phrase: '9 to 5 UTC', sample: 'The desk is open 9 to 5 UTC.' },
    urdu: { name: 'Roman Urdu handoff', prompt: 'Mujhe support team se baat karni hai.', route: 'handoff', phrase: 'support team', sample: 'Main aap ko support team se mila rahi hoon.' },
  };
  function grader(root) {
    root.textContent = '';
    let id = 'refund', picked = 'handoff';
    const prompt = el('div', { class: 'slip' });
    const reply = el('textarea', { rows: '2', id: 'grade-in' });
    const out = el('div', { class: 'big', 'aria-live': 'polite' });
    const why = el('div', { class: 'pass-fail' });
    const routes = seg('Route chosen by the assistant', [['reply', 'Reply'], ['handoff', 'Hand off to a person']], picked, (v) => { picked = v; run(); });
    const run = () => {
      const c = GRADES[id];
      // grade_answer(): route must equal the expected route and the reply must contain the phrase, ignoring case.
      const okRoute = picked === c.route, okPhrase = reply.value.toLowerCase().includes(c.phrase.toLowerCase());
      const pass = okRoute && okPhrase;
      out.className = 'big ' + (pass ? 'is-wax' : 'is-red');
      out.replaceChildren(pass ? 'Pass' : 'Fail', el('small', { text: pass ? 'Both conditions hold' : 'The gate exits 1 if any case fails' }));
      why.replaceChildren(
        el('span', { class: okRoute ? 'ok' : 'no', text: `Route is “${c.route}”` }),
        el('span', { class: okPhrase ? 'ok' : 'no', text: `Reply contains “${c.phrase}”` }));
    };
    const load = (k) => { id = k; const c = GRADES[k]; prompt.textContent = c.prompt; reply.value = c.sample; picked = c.route; routes.set(picked); run(); };
    reply.addEventListener('input', run);
    root.append(edge('Support answer grader', 'Three fictional cases'),
      el('div', { class: 'row' }, seg('Case', Object.entries(GRADES).map(([k, c]) => [k, c.name]), id, load)),
      el('div', { class: 'field' }, el('span', { class: 'lab', text: 'Customer message' }), prompt),
      el('div', { class: 'field' }, el('span', { class: 'lab', text: 'Route chosen by the assistant' }), el('div', {}, routes)),
      el('div', { class: 'field' }, el('label', { for: 'grade-in', text: 'Assistant reply' }), reply),
      el('div', { class: 'row' }, out), why,
      el('p', { class: 'note', text: 'Change the route or delete the required phrase and the case fails. The scorer checks only these two things, which is the limit the page describes.' }));
    load(id);
  }

  const DEMOS = { takes, scan, gate, proofs, router, grader, fold };
  document.querySelectorAll('[data-demo]').forEach((n) => {
    try { DEMOS[n.dataset.demo]?.(n, n.dataset.mode === 'full'); } catch (e) { console.error(e); }
  });
})();
