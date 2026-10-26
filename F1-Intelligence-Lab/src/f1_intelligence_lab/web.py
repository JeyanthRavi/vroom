"""Static, dependency-free landing page for the F1 Intelligence Lab."""

HOME_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Two evidence-linked Formula 1 multi-agent research projects in one local lab.">
  <title>F1 Intelligence Lab</title>
  <style>
:root{color-scheme:dark;--bg:#101014;--night:#101014;--panel:#19191f;--raised:#212129;--line:#35353e;--ink:#f5f5f7;--paper:#f5f5f7;--muted:#a9a9b5;--red:#f33b40;--acid:#ff686c;--lime:#b8f28b;--cyan:#64d8ff;--mono:ui-monospace,SFMono-Regular,Consolas,monospace;--display:"Arial Narrow","Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}body:before{content:"";display:block;height:5px;background:var(--red)}a{color:inherit}button,select,input{font:inherit}button,a,select,summary{-webkit-tap-highlight-color:transparent}a:focus-visible,button:focus-visible,summary:focus-visible{outline:2px solid #fff;outline-offset:5px}button{cursor:pointer}button:disabled{opacity:.55;cursor:wait}h1,h2,h3,p{overflow-wrap:break-word}h1,h2,h3{font-family:var(--display)}.lab-nav{width:min(1240px,calc(100% - 64px));margin:auto;display:flex;align-items:center;justify-content:space-between;gap:24px;min-height:78px;border-bottom:1px solid var(--line);font:11px var(--mono);text-transform:uppercase;letter-spacing:.06em}.lab-nav>a:first-child{font:850 14px var(--display);letter-spacing:-.02em;color:var(--ink)}.lab-nav>a:first-child:before{content:"";display:inline-block;width:25px;height:14px;background:repeating-linear-gradient(0deg,transparent 0 3px,var(--red) 3px 6px);transform:skewX(-30deg);margin-right:12px}.lab-nav a{text-decoration:none;display:inline-flex;align-items:center;min-height:48px;color:var(--muted)}.lab-nav span{display:flex;gap:26px}.lab-nav a:hover{color:#fff}.lab-nav [aria-current="page"]{color:#fff;box-shadow:inset 0 -3px var(--red)}.eyebrow,.kicker{font:11px/1.5 var(--mono);letter-spacing:.15em;text-transform:uppercase;color:#ff777b}.eyebrow:before,.kicker:before{content:"";display:inline-block;width:22px;height:3px;background:var(--red);vertical-align:middle;margin-right:10px}.lab-footer{max-width:1240px;margin:32px auto 0;padding:25px 0;border-top:1px solid var(--line);font:11px/1.7 var(--mono);color:var(--muted)}@media(max-width:760px){.lab-nav{width:calc(100% - 32px);gap:12px;flex-wrap:wrap;padding:12px 0}.lab-nav span{gap:18px}.lab-nav a{min-height:40px}.lab-nav>a:first-child{font-size:12px}.lab-footer{margin:28px 16px 0}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{transition:none!important;animation:none!important}}

.wrap{width:min(1240px,calc(100% - 64px));margin:auto}.wrap nav{min-height:78px;display:flex;justify-content:space-between;align-items:center;gap:24px;border-bottom:1px solid var(--line)}.brand{text-decoration:none;font:850 14px var(--display);letter-spacing:-.02em}.brand b{font-size:29px;color:var(--red);font-style:italic;margin-right:10px;letter-spacing:-3px}nav ul{display:flex;gap:30px;list-style:none;margin:0;padding:0}nav li a{display:inline-flex;align-items:center;min-height:48px;color:var(--muted);text-decoration:none;font:11px var(--mono);text-transform:uppercase}nav li a:hover{color:white}.hero{display:grid;grid-template-columns:1fr 1fr;gap:70px;padding:64px 0 60px;align-items:center}.hero h1{font-size:clamp(55px,6.5vw,92px);line-height:.92;letter-spacing:-.065em;font-weight:950;font-style:italic;margin:24px 0;text-transform:uppercase}.hero h1 span{color:var(--red)}.hero-copy{max-width:455px;color:var(--muted);font-size:15px;line-height:1.8}.hero-actions{display:flex;gap:12px;flex-wrap:wrap;margin-top:30px}.cta{display:inline-flex;align-items:center;justify-content:center;min-height:48px;padding:12px 21px;background:#d91f2a;color:#fff;border:1px solid #d91f2a;border-radius:3px;text-decoration:none;font-size:12px;font-weight:750;transition:background .2s,transform .2s}.cta:hover{background:#f33b40;transform:translateY(-2px)}.cta.secondary{background:transparent;border-color:#555560}.cta.secondary:hover{background:var(--raised)}.preview{border:1px solid var(--line);border-top:4px solid var(--red);border-radius:3px 22px 3px 3px;overflow:hidden;background:#16161c}.preview-head{display:flex;justify-content:space-between;gap:12px;padding:18px 22px;background:#202028;font:10px var(--mono);letter-spacing:.07em}.preview-head span{color:#ff9296}.circuit{padding:12px 22px;background:repeating-linear-gradient(0deg,transparent 0 27px,#ffffff04 27px 28px)}.circuit svg{display:block;width:100%;height:215px}.circuit p{font:9px var(--mono);color:var(--muted);letter-spacing:.08em}.timing{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line)}.timing div{padding:20px 15px}.timing div+div{border-left:1px solid var(--line)}.timing small{display:block;font:10px var(--mono);color:var(--muted);letter-spacing:.06em}.timing strong{display:block;font:750 26px var(--mono);letter-spacing:-.06em;margin-top:10px}.preview-caption{display:flex;justify-content:space-between;gap:12px;padding:11px 20px;background:#24242c;font:10px var(--mono);color:#d0d0da}.preview-caption b{color:#fff}.section-head{border-top:8px solid var(--line);border-right:8px solid var(--line);border-radius:0 28px 0 0;padding:30px 24px 26px 0;display:flex;justify-content:space-between;gap:25px;align-items:end;margin-top:8px}.section-head h2{margin:0;font-weight:900;font-size:34px;line-height:1.05;letter-spacing:-.045em;text-transform:uppercase}.section-head p{max-width:370px;color:var(--muted);font-size:13px;margin:0}.projects{display:grid;grid-template-columns:1fr 1fr;gap:24px;padding:4px 0 56px}.project{display:flex;flex-direction:column;position:relative;overflow:hidden;border:1px solid var(--line);border-radius:4px 22px 4px 4px;background:var(--panel);padding:30px;min-height:365px;transition:border-color .2s,transform .2s}.project:hover{border-color:var(--red);transform:translateY(-3px)}.project:after{content:attr(data-number);position:absolute;right:20px;top:30px;color:#ffffff;font:italic 950 108px/.9 var(--display);pointer-events:none;opacity:.1}.tag{font:10px var(--mono);text-transform:uppercase;letter-spacing:.1em;color:#ff9397;border-left:3px solid var(--red);padding-left:10px;max-width:80%}.project h3{font-size:39px;text-transform:uppercase;font-weight:900;font-style:italic;line-height:1;margin:48px 0 16px;letter-spacing:-.04em;z-index:1}.project p{font-size:14px;color:var(--muted);margin:0;max-width:460px}.agents{display:flex;flex-wrap:wrap;gap:8px;margin-top:auto;padding:24px 0}.agents span{font:10px var(--mono);padding:6px 8px;background:#24242c;color:#c7c7d1;border-radius:2px}.launch{display:flex;justify-content:space-between;align-items:center;padding-top:17px;border-top:1px solid var(--line);text-decoration:none;font-size:13px;font-weight:750}.launch b{font-size:24px;color:var(--red)}.protocol{display:grid;grid-template-columns:repeat(3,1fr);gap:28px;padding-bottom:40px}.protocol article{padding:20px 0;border-top:1px solid var(--line)}.protocol strong{font-size:14px;display:block;margin-bottom:8px}.protocol p{font-size:13px;color:var(--muted);margin:0}.warning{background:#17171c;border-top:1px solid var(--line);padding:24px 0;color:var(--muted);font-size:11px}.warning .wrap{display:grid;grid-template-columns:150px 1fr;gap:30px}.warning strong{font:10px var(--mono);letter-spacing:.08em;color:#dedee5}.warning p{margin:0}footer{padding:22px 0 32px;font:10px var(--mono);color:var(--muted)}footer .wrap{display:flex;justify-content:space-between;gap:20px}footer a{text-decoration:none}.runner{display:none}@media(max-width:900px){.hero{gap:30px}.timing strong{font-size:21px}.preview-head{flex-wrap:wrap}.project h3{font-size:33px}}@media(max-width:760px){.wrap{width:calc(100% - 32px)}.wrap nav{flex-wrap:wrap;padding:14px 0;gap:8px}nav ul{gap:22px}nav li a{font-size:10px;min-height:36px}.hero{grid-template-columns:1fr;gap:32px;padding:35px 0 40px}.hero h1{font-size:clamp(54px,12vw,80px)}.circuit svg{height:190px}.section-head{display:block;border-width:5px;padding-top:23px}.section-head p{margin-top:16px}.section-head h2{font-size:29px}.projects,.protocol{grid-template-columns:1fr}.project{padding:24px;min-height:350px}.project h3{font-size:36px}.protocol{gap:0}.warning .wrap{grid-template-columns:1fr;gap:10px}footer .wrap{flex-wrap:wrap}.timing strong{font-size:22px}}
</style>
</head>
<body>
  <header class="wrap">
    <nav aria-label="Primary navigation">
      <a class="brand" href="/"><b>F1</b> INTELLIGENCE LAB</a>
      <ul>
        <li><a href="#projects">Projects</a></li>
        <li><a href="/stewardlens/">StewardLens</a></li>
        <li><a href="/telemetry/">Telemetry</a></li>
        <li><a href="/docs">API</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <section class="hero wrap">
      <div>
        <div class="kicker">THE INDEPENDENT F1 ANALYSIS LAB</div>
        <h1>READ<br>BETWEEN<br><span>THE LAPS.</span></h1>
        <p class="hero-copy">Go beyond the timing screen. Explore the evidence behind a ruling, or find where two drivers make the difference.</p>
        <div class="hero-actions"><a class="cta" href="/telemetry/">Compare laps ↗</a><a class="cta secondary" href="/stewardlens/">Explore incidents ↗</a></div>
      </div>
      <div class="preview"><div class="preview-head">MONZA / 2024 / QUALIFYING <span>CACHED SESSION</span></div><div class="circuit"><svg viewBox="0 0 500 220" fill="none" role="img" aria-label="Illustrative circuit showing braking and traction analysis"><path id="circuit-route" d="M60 165 L135 50 Q145 34 170 38 L360 68 Q388 72 402 95 L439 150 Q452 173 427 182 L340 190 L298 167 L260 174 L232 146 L180 151 L150 174 L80 187 Q49 189 60 165Z" stroke="#3d3036" stroke-width="18" stroke-linejoin="round"/><use href="#circuit-route" stroke="#ff555b" stroke-width="2"/><use class="runner" href="#circuit-route" stroke="#fff" stroke-width="6" stroke-linecap="round"/><circle cx="135" cy="50" r="5" fill="#fff"/><text x="108" y="22" fill="#c8c8d2" font-family="monospace" font-size="10">BRAKING</text><circle cx="298" cy="167" r="5" fill="#f33b40"/><text x="280" y="140" fill="#c8c8d2" font-family="monospace" font-size="10">TRACTION</text></svg><p>ILLUSTRATIVE CIRCUIT · RECORDED LAP TIMES BELOW</p></div><div class="timing"><div><small>NORRIS</small><strong>1:19.327</strong></div><div><small>PIASTRI</small><strong>1:19.436</strong></div><div><small>DIFFERENCE</small><strong style="color:#b8f28b">−0.109 s</strong></div></div><div class="preview-caption"><span><b>NOR × PIA</b> / LAP COMPARISON</span><span>OPENF1 DATA</span></div></div>
    </section>

    <section class="wrap" id="projects">
      <div class="section-head">
        <h2>CHOOSE YOUR<br>WORKSTATION.</h2>
        <p>Pick a question. Open a workbench. Follow the evidence all the way through.</p>
      </div>
      <div class="projects">
        <article class="project" data-number="01">
          <span class="tag">Verified FIA archive · agent demo</span>
          <h3>Steward&shy;Lens</h3>
          <p>Reconstruct an incident, retrieve relevant rules and precedents, hear both drivers' cases, and inspect a simulated steward verdict.</p>
          <div class="agents" aria-label="StewardLens agent roles">
            <span>Evidence</span><span>Regulations</span><span>Precedent</span><span>Advocates</span><span>Bias audit</span>
          </div>
          <a class="launch" href="/stewardlens/"><span>Open case library</span><b aria-hidden="true">↗</b></a>
        </article>
        <article class="project" data-number="02">
          <span class="tag">Recorded telemetry · lap comparison</span>
          <h3>Telemetry Pit Crew</h3>
          <p>Compare two laps through braking, cornering, traction and straight-line specialists, then receive a prioritized race-engineering debrief.</p>
          <div class="agents" aria-label="Telemetry agent roles">
            <span>Braking</span><span>Cornering</span><span>Traction</span><span>Straight-line</span><span>Chief engineer</span>
          </div>
          <a class="launch" href="/telemetry/"><span>Open telemetry lab</span><b aria-hidden="true">↗</b></a>
        </article>
      </div>
    </section>

    <section class="wrap" aria-labelledby="protocol-title">
      <div class="section-head">
        <h2 id="protocol-title">THE ENGINEERING BRIEF.</h2>
        <p>Explore the sources, understand the reasoning, and see where the data reaches its limits.</p>
      </div>
      <div class="protocol">
        <article><strong>01 · Compute first</strong><p>Numerical features are calculated deterministically before agents interpret them.</p></article>
        <article><strong>02 · Cite the packet</strong><p>Claims point back to supplied evidence or regulations; missing data stays visible.</p></article>
        <article><strong>03 · Test the decision</strong><p>Structured outputs, reproducible fixtures and automated tests make disagreement inspectable.</p></article>
      </div>
    </section>

    <aside class="warning">
      <div class="wrap">
        <strong>Research status</strong>
        <p>This research site mixes checksum-verified public FIA documents with clearly marked demonstration data. It is not live timing, does not represent Formula 1 or the FIA, and must not be treated as an official stewarding or engineering system.</p>
      </div>
    </aside>
  </main>

  <footer><div class="wrap"><span>F1 Intelligence Lab · local prototype</span><span><a href="/health">System health</a> · <a href="/docs">Portal API</a></span></div></footer>
</body>
</html>
"""

