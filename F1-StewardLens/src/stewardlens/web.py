"""Dependency-free browser interface for StewardLens."""

INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StewardLens</title>
  <style>
:root{color-scheme:dark;--bg:#101014;--night:#101014;--panel:#19191f;--raised:#212129;--line:#35353e;--ink:#f5f5f7;--paper:#f5f5f7;--muted:#a9a9b5;--red:#f33b40;--acid:#ff686c;--lime:#b8f28b;--cyan:#64d8ff;--mono:ui-monospace,SFMono-Regular,Consolas,monospace;--display:"Arial Narrow","Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}body:before{content:"";display:block;height:5px;background:var(--red)}a{color:inherit}button,select,input{font:inherit}button,a,select,summary{-webkit-tap-highlight-color:transparent}a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid #fff;outline-offset:5px}button{cursor:pointer}button:disabled{opacity:.55;cursor:wait}h1,h2,h3,p{overflow-wrap:break-word}h1,h2,h3{font-family:var(--display)}.lab-nav{width:min(1240px,calc(100% - 64px));margin:auto;display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:78px;border-bottom:1px solid var(--line);font:11px var(--mono);text-transform:uppercase;letter-spacing:.06em}.lab-nav>a:first-child{font:850 14px var(--display);letter-spacing:-.02em;color:var(--ink)}.lab-nav>a:first-child:before{content:"";display:inline-block;width:25px;height:14px;background:repeating-linear-gradient(0deg,transparent 0 3px,var(--red) 3px 6px);transform:skewX(-30deg);margin-right:12px}.lab-nav a{text-decoration:none;display:inline-flex;align-items:center;min-height:48px;color:var(--muted)}.lab-nav span{display:flex;gap:20px;flex-wrap:wrap}.lab-nav a:hover{color:#fff}.lab-nav [aria-current="page"]{color:#fff;box-shadow:inset 0 -3px var(--red)}.eyebrow,.kicker{font:11px/1.5 var(--mono);letter-spacing:.15em;text-transform:uppercase;color:#ff777b}.eyebrow:before,.kicker:before{content:"";display:inline-block;width:22px;height:3px;background:var(--red);vertical-align:middle;margin-right:10px}.lab-footer{max-width:1240px;margin:32px auto 0;padding:25px 0;border-top:1px solid var(--line);font:11px/1.7 var(--mono);color:var(--muted)}@media(max-width:760px){.lab-nav{width:calc(100% - 32px);gap:12px;flex-wrap:wrap;padding:12px 0}.lab-nav span{gap:18px}.lab-nav a{min-height:40px}.lab-nav>a:first-child{font-size:12px}.lab-footer{margin:28px 16px 0}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{transition:none!important;animation:none!important}}

header,main{width:min(1240px,calc(100% - 64px));margin:auto}header{position:relative;padding:40px 0 28px;border-bottom:1px solid var(--line);margin-bottom:26px}header:after{content:"01";position:absolute;right:12px;top:26px;font:italic 950 130px/1 var(--display);color:#ffffff08;pointer-events:none}h1{font-size:clamp(42px,5.5vw,68px);font-style:italic;font-weight:950;text-transform:uppercase;letter-spacing:-.06em;line-height:1.05;margin:12px 0 16px}.lede{max-width:680px;color:var(--muted);font-size:14px;line-height:1.75;margin:0}.notice{color:#bcbcc8;font-size:11px;border-left:3px solid var(--red);padding:0 12px;margin:16px 0 0}.grid{display:grid;grid-template-columns:340px minmax(0,1fr);gap:24px;padding-bottom:40px;align-items:start}.panel{background:var(--panel);border:1px solid var(--line);border-radius:3px 18px 3px 3px;padding:24px}.panel>h2,.archive>h2{font:700 11px var(--mono);letter-spacing:.1em;text-transform:uppercase;margin:0 0 20px;display:flex;align-items:center;gap:10px}.panel>h2:before,.archive>h2:before{content:"";width:5px;height:12px;background:var(--red)}button{width:100%;text-align:left;color:var(--ink);background:#212128;border:1px solid #393942;border-radius:3px;padding:16px;margin:0 0 10px;transition:background .2s,border-color .2s}button:hover{background:#2b232a;border-color:#bd4c54}button strong{display:block;font-size:13px;line-height:1.6}button span{display:block;font-size:11px;color:var(--muted);line-height:1.6;margin-top:5px}#cases button[aria-pressed="true"]{background:#302128;border-color:var(--red);box-shadow:inset 3px 0 var(--red)}.meta{font-size:12px;line-height:1.7;color:var(--muted)}.archive{margin-top:26px;border-top:1px solid var(--line);padding-top:23px}.archive-card{display:block;padding:14px 0;text-decoration:none;border-bottom:1px solid var(--line)}.archive-card strong{font:700 12px var(--mono);color:#ff9da0;display:block}.archive-card strong:after{content:" ↗"}.archive-card span{display:block;font-size:11px;margin-top:6px}.archive-card:hover strong{color:#fff}.empty{min-height:390px;display:grid;place-items:center;text-align:center;background:repeating-linear-gradient(135deg,transparent 0 10px,#ffffff02 10px 11px);border:1px dashed #41414b;border-radius:3px}.empty p{max-width:300px;color:var(--muted);font-size:13px;padding:24px}.empty p:before{content:"RACE CONTROL";display:block;font:900 italic 30px var(--display);color:#f5f5f7;margin-bottom:16px;letter-spacing:-.04em}.empty p:after{content:"AWAITING CASE SELECTION";display:block;color:#ff858a;font:9px var(--mono);letter-spacing:.12em;margin-top:22px}.primary{width:auto;padding:13px 22px;background:#d91f2a;border-color:#d91f2a;color:#fff;font-size:12px;font-weight:750;margin:18px 0 0}.primary:hover{background:var(--red)}#room>h2{font-size:20px;text-transform:uppercase;letter-spacing:-.02em;margin:24px 0 14px}#room>p{font-size:14px}#room ul{padding:0;list-style:none}#room li{position:relative;background:#202027;border-left:2px solid #555562;margin:12px 0;padding:14px 18px;font-size:13px}#room li strong{font-weight:600}.verdict{margin-top:24px;padding:24px;border:1px solid #754048;border-top:4px solid var(--red);background:#221c22;border-radius:3px 15px 3px 3px}.verdict h3{text-transform:uppercase;font-weight:900;font-style:italic;font-size:32px;letter-spacing:-.03em;margin:10px 0}.verdict p{font-size:13px}.verdict .eyebrow{font-size:10px}code{font-size:11px;overflow-wrap:anywhere}a{color:inherit}@media(max-width:760px){header,main{width:calc(100% - 32px)}header{padding-top:28px}header:after{font-size:80px}.grid{grid-template-columns:1fr;gap:18px}.panel{padding:20px}.empty{min-height:260px}h1{font-size:44px}.lede{font-size:13px}}
</style>
</head>
<body>
  <nav class="lab-nav" aria-label="Lab navigation"><a href="/">↖ F1 ECOSYSTEM</a><span><a href="/pitwall/">Replay</a><a href="/scoutgrid/">ScoutGrid</a><a href="/claimcheck/">ClaimCheck</a><a href="/stewardlens/" aria-current="page">StewardLens</a><a href="/telemetry/">Telemetry ↗</a></span></nav>
  <header>
    <div class="eyebrow">01 / RACE CONTROL WORKSTATION</div>
    <h1>STEWARD<span style="color:var(--red)">LENS</span></h1>
    <p class="lede">Open an F1 incident, inspect its evidence packet, and ask a team of specialist agents for a transparent simulated ruling.</p>
    <p class="notice">Educational research prototype — not an official FIA decision system.</p>
  </header>
  <main class="grid">
    <section class="panel">
      <h2>Case library</h2>
      <div id="cases"><span class="meta">Loading incidents…</span></div>
      <div class="archive">
        <h2>Verified FIA archive</h2>
        <div id="fia"><span class="meta">Loading official documents…</span></div>
      </div>
    </section>
    <section class="panel" id="room">
      <div class="empty"><p>Select a case from the library to inspect the evidence and run a simulated ruling.</p></div>
    </section>
  </main>
  <script>
    const cases = document.querySelector('#cases');
    const fia = document.querySelector('#fia');
    const room = document.querySelector('#room');
    const escapeHtml = value => String(value ?? '').replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));

    async function request(path, options) {
      const response = await fetch(path, options);
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${response.status})`);
      }
      return response.json();
    }

    async function loadCases() {
      try {
        const incidents = await request('/incidents');
        cases.innerHTML = incidents.length ? incidents.map(item => `
          <button type="button" data-incident-id="${escapeHtml(item.id)}">
            <strong>${escapeHtml(item.event)} · Lap ${escapeHtml(item.lap)}</strong>
            <span>${escapeHtml(item.driver_a)} vs ${escapeHtml(item.driver_b)} · ${escapeHtml(item.season)}</span>
          </button>`).join('') : '<span class="meta">No sample incidents are loaded.</span>';
        cases.querySelectorAll('[data-incident-id]').forEach(button => {
          button.addEventListener('click', () => openCase(button.dataset.incidentId));
        });
      } catch (error) { cases.innerHTML = `<span class="meta">${escapeHtml(error.message)}</span>`; }
    }

    async function loadFiaDecisions() {
      try {
        const decisions = await request('/fia-decisions');
        fia.innerHTML = decisions.length ? decisions.map(item => `
          <a class="archive-card" href="${escapeHtml(item.source_document_url)}" target="_blank" rel="noopener noreferrer">
            <strong>Doc ${escapeHtml(item.document_number)} · Car ${escapeHtml(item.driver_number)}</strong>
            <span class="meta">${escapeHtml(item.driver_name)} · ${escapeHtml(item.event)} · ${escapeHtml(item.decision)}</span>
          </a>`).join('') : '<span class="meta">No verified FIA documents are cached.</span>';
      } catch (error) { fia.innerHTML = `<span class="meta">${escapeHtml(error.message)}</span>`; }
    }

    async function openCase(id) {
      cases.querySelectorAll('[data-incident-id]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.incidentId === id)));
      room.innerHTML = '<div class="empty"><p>Loading evidence…</p></div>';
      try {
        const packet = await request(`/incidents/${encodeURIComponent(id)}/evidence`);
        const item = packet.incident;
        room.innerHTML = `
          <div class="eyebrow">${escapeHtml(item.session)} · ${escapeHtml(item.season)}</div>
          <h2 style="font-size:1.7rem;margin-top:6px">${escapeHtml(item.driver_a)} vs ${escapeHtml(item.driver_b)}</h2>
          <p>${escapeHtml(item.summary)}</p>
          <p class="meta">${escapeHtml(item.event)} · Lap ${escapeHtml(item.lap)} · ${escapeHtml(item.category)}</p>
          <h2>Evidence</h2>
          <ul>${packet.evidence.map(e => `<li><strong>${escapeHtml(e.summary)}</strong><br><span class="meta">${escapeHtml(e.kind)} · quality ${Math.round(e.quality*100)}% · ${escapeHtml(e.source)}</span></li>`).join('')}</ul>
          <button class="primary" id="deliberate">Run agent deliberation</button>
          <div id="result" role="status" aria-live="polite"></div>`;
        document.querySelector('#deliberate').onclick = () => deliberateCase(id);
      } catch (error) { room.innerHTML = `<div class="empty"><p>${escapeHtml(error.message)}</p></div>`; }
    }

    async function deliberateCase(id) {
      const button = document.querySelector('#deliberate');
      const result = document.querySelector('#result');
      button.disabled = true; button.textContent = 'Agents deliberating…';
      try {
        const run = await request(`/incidents/${encodeURIComponent(id)}/deliberate`, {method:'POST'});
        const verdict = run.verdict;
        result.innerHTML = `<article class="verdict">
          <span class="eyebrow">Confidence ${Math.round(verdict.confidence*100)}%</span>
          <h3>${escapeHtml(verdict.decision.replaceAll('_',' '))}</h3>
          <p>${verdict.findings.map(escapeHtml).join(' ')}</p>
          <p class="meta">Penalty: ${escapeHtml(verdict.penalty_category.replaceAll('_',' '))} · Run <code>${escapeHtml(run.id)}</code></p>
        </article>`;
      } catch (error) { result.innerHTML = `<p class="notice">${escapeHtml(error.message)}</p>`; }
      finally { button.disabled = false; button.textContent = 'Run again'; }
    }
    loadCases();
    loadFiaDecisions();
  </script>
</body>
</html>
"""

