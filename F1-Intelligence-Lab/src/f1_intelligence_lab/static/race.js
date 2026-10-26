'use strict';
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const colors = ['#ff8177','#80d7f5','#d2ed8a','#dcb0ff','#ffca80'];
const compounds = {SOFT:'#ff8177',MEDIUM:'#f2d77c',HARD:'#e8e8e4',INTERMEDIATE:'#91d8a4',WET:'#80b9f5',UNKNOWN:'#adb1bd'};
let data, selected = new Set(), busy = false;
document.querySelector('.import-panel > div > p').textContent='Import one race as CSV. It is sent to this local server for analysis and is not saved by the application. Refresh returns to a saved historical race when available. Use the session library for persistent provider imports.';
const fmt = n => n == null ? '—' : n.toFixed(3);
const depth = () => document.querySelector('input[name=depth]:checked').value;
function save(name, contents, type) {
  const url = URL.createObjectURL(new Blob([contents], {type}));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function metric(title, value, note) { return `<div class="metric"><small>${esc(title)}</small><strong>${esc(value)}</strong><span>${esc(note)}</span></div>`; }
function render() {
  $('analysis').hidden = false;
  $('raceName').textContent = data.name;
  $('source').textContent = data.source_type === 'synthetic' ? 'SYNTHETIC EXERCISE / NOT A REAL GRAND PRIX' : data.source_type.endsWith('_historical') ? 'HISTORICAL '+data.source_type.split('_')[0].toUpperCase()+' DATA / LOCALLY CACHED' : 'USER IMPORT / NOT INDEPENDENTLY VERIFIED';
  $('coverage').textContent = `${data.drivers.length} drivers · ${data.records} observed laps · laps through ${data.max_lap} · deterministic analysis`;
  document.querySelector('.notes-panel > .subtle').textContent = data.source_type.endsWith('_historical') ? 'Historical provider data. Missing records and inferred flags are not independently certified.' : 'Import labels and flags are supplied by you, not independently verified.';
  document.querySelector('.outline-number').textContent = data.max_lap;
  const count = data.drivers.reduce((n,d)=>n+d.clean_laps,0);
  const pits = data.drivers.reduce((n,d)=>n+d.pit_laps.length,0);
  $('metrics').innerHTML = metric('Observed drivers',data.drivers.length,'Not a full-field classification') + metric('Eligible laps',count,`${data.records-count} excluded from pace stats`) + metric('Marked pit-in laps',pits,'As supplied in the dataset') + metric('Last observed lap',data.max_lap,'Coverage is not race distance');
  $('driverControls').innerHTML = data.drivers.map((d,i)=>`<label><input type="checkbox" data-driver="${esc(d.driver)}" ${selected.has(d.driver)?'checked':''}><span class="swatch" style="background:${colors[i%colors.length]}"></span>${esc(d.driver)}</label>`).join('');
  $('driverControls').querySelectorAll('input').forEach(input => input.onchange = () => {
    if (input.checked) selected.add(input.dataset.driver); else selected.delete(input.dataset.driver);
    renderChart();
  });
  $('stints').innerHTML = data.drivers.map(d=>`<div class="stint-row"><span class="stint-name">${esc(d.driver)}</span><div class="stint-track" style="grid-template-columns:repeat(${data.max_lap},minmax(0,1fr))">${d.laps.map(r=>`<span class="lap-block ${r.pit?'pit':''}" style="grid-column:${r.lap};background:${compounds[r.compound]}" title="${esc(d.driver)} · lap ${r.lap} · ${r.compound} · stint ${r.stint}${r.pit?' · pit-in':''}">${data.max_lap<=40?(r.compound==='UNKNOWN'?'?':r.compound[0]):''}</span>`).join('')}</div></div>`).join('')+`<div class="stint-axis"><span>LAP 1</span><span>LAP ${data.max_lap}</span></div>`;
  $('stintRows').innerHTML = data.drivers.flatMap(d=>d.stints.map(s=>`<tr><td>${esc(d.driver)} / ${s.stint}</td><td>${esc(s.compound)}</td><td>${s.clean_laps}</td><td>${fmt(s.median)}</td><td>${s.trend==null?'—':(s.trend>=0?'+':'')+s.trend.toFixed(3)}</td></tr>`)).join('');
  const messages = [...data.warnings];
  if(data.source_type==='synthetic') messages.unshift('Fictional drivers and lap times. Use this exercise to learn the controls, not to draw conclusions about F1 teams.');
  messages.push('Neutralized, pit-in, following out-laps and opening laps are excluded from eligible pace. Traffic and driver errors may remain.');
  messages.push('Different lap windows and tyre choices make raw medians unsuitable as a driver ranking.');
  $('warnings').innerHTML = messages.map(m=>`<li>${esc(m)}</li>`).join('');
  $('method').innerHTML = `<p><strong>Method ${esc(data.methodology.version)} · ${esc(data.source_type)}</strong></p><p>${esc(data.methodology.clean_laps)}</p><p>${esc(data.methodology.trend)}</p><p>${esc(data.methodology.comparison)}</p><p>Original CSV SHA-256: <code>${esc(data.sha256)}</code>. Identifies the imported bytes; does not certify accuracy or provenance.</p>`;
  $('tableDriver').innerHTML = data.drivers.map(d=>`<option>${esc(d.driver)}</option>`).join('');
  if(data.provenance)$('method').insertAdjacentHTML('beforeend',`<p>Provider: ${esc(data.provenance.provider)} · session ${esc(data.provenance.session_key)} · retrieved ${esc(data.provenance.retrieved_at)}. Full source URLs are included in the exported JSON.</p>`);
  renderLaps(); renderBrief(); renderChart();
}
function renderBrief() {
  if(!data)return;
  const stops = data.drivers.map(d=>`${d.driver}: ${d.pit_laps.length?'lap '+d.pit_laps.join(', '):'no marked pit-in'}`);
  $('briefTitle').textContent = depth()==='beginner' ? 'Start with the shape, not the winner.' : 'Compare observations. Resist causal claims.';
  $('briefBody').innerHTML = depth()==='beginner'
    ? `<p>The traces show how long each lap took. Lower points mean faster laps. Turn off “eligible laps only” to see slow pit and safety-car laps.</p><p>The tyre rows show when each driver changed stints. A later stop is a different choice—not automatically a worse one.</p><ul>${stops.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`
    : `<p>Pace statistics use each driver’s own GREEN laps, excluding lap 1, pit-in and following out-laps. Filtering the chart does not change these statistics.</p><p>The stint trend is an unadjusted OLS slope. Fuel burn, traffic, track evolution and tyre state are confounded. At least three eligible samples are required.</p><p>No cumulative race gaps are constructed from incomplete lap coverage.</p>`;
}
function renderLaps() {
  if(!data)return;
  const d=data.drivers.find(d=>d.driver===$('tableDriver').value);
  $('lapRows').innerHTML = d.laps.map(r=>`<tr><td>${r.lap}</td><td>${fmt(r.lap_time)}</td><td>${r.stint}</td><td>${esc(r.compound)}</td><td>${esc(r.flag)}</td><td>${r.pit?'Yes':'No'}</td><td>${r.clean?'Yes':'No'}</td></tr>`).join('');
}
function renderChart() {
  if(!data)return;
  const clean=$('clean').checked;
  const visible=data.drivers.filter(d=>selected.has(d.driver));
  const values=visible.flatMap(d=>d.laps.filter(r=>!clean||r.clean).map(r=>r.lap_time));
  if(!values.length){$('chart').innerHTML='<p class="subtle">No visible eligible laps. Select a driver or turn off the eligible-lap filter.</p>';return;}
  const w=800,h=300,left=54,right=18,top=16,bottom=34;
  const min=Math.min(...values)-.5,max=Math.max(...values)+.5;
  const x=lap=>left+(lap-1)/Math.max(1,data.max_lap-1)*(w-left-right);
  const y=t=>h-bottom-(t-min)/(max-min)*(h-top-bottom);
  let svg=`<svg viewBox="0 0 ${w} ${h}" aria-hidden="true"><rect width="${w}" height="${h}" fill="#101114"/>`;
  for(let i=0;i<=4;i++){
    const time=min+(max-min)*i/4,py=y(time);
    svg+=`<line x1="${left}" y1="${py}" x2="${w-right}" y2="${py}" stroke="#33363e"/><text x="${left-8}" y="${py+4}" text-anchor="end" fill="#b1b6c2" font-size="11" font-family="monospace">${time.toFixed(1)}</text>`;
  }
  const ticks=[...new Set([1,Math.round(data.max_lap/4),Math.round(data.max_lap/2),Math.round(data.max_lap*3/4),data.max_lap])].filter(n=>n>=1);
  ticks.forEach(lap=>{svg+=`<text x="${x(lap)}" y="${h-9}" fill="#b1b6c2" text-anchor="middle" font-size="11" font-family="monospace">${lap}</text>`});
  visible.forEach(d=>{
    const index=data.drivers.indexOf(d),color=colors[index%colors.length];let prev=null,path='';
    d.laps.forEach(r=>{
      if(clean&&!r.clean){prev=null;return;}
      const px=x(r.lap),py=y(r.lap_time);
      path+=`${prev&&prev.lap===r.lap-1?'L':'M'}${px},${py} `;
      svg+=`<circle cx="${px}" cy="${py}" r="2.5" fill="${color}"><title>${esc(d.driver)} · lap ${r.lap} · ${r.lap_time.toFixed(3)} s · ${esc(r.flag)}</title></circle>`;
      prev=r;
    });
    svg+=`<path d="${path}" fill="none" stroke="${color}" stroke-width="2" ${index%2?'stroke-dasharray="6 3"':''}/>`;
  });
  $('chart').innerHTML=svg+'</svg>';
}
async function load(url, options) {
  if(busy)return;
  busy=true; $('error').hidden=true; $('status').textContent='Analyzing lap records…';
  $('importButton').disabled=true;$('reset').disabled=true;$('export').disabled=true;
  $('savedRace').disabled=true;
  const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),20000);
  try{
    const response=await fetch(url,{...options,signal:controller.signal});const result=await response.json();
    if(!response.ok)throw new Error(typeof result.detail==='string'?result.detail:'Check the name and CSV size/format, then retry.');
    data=result;selected=new Set(data.drivers.slice(0,5).map(d=>d.driver));render();
    $('status').textContent=`Loaded ${data.records} lap records. ${data.source_type==='synthetic'?'Synthetic exercise.':data.source_type.endsWith('_historical')?'Historical session loaded from local storage.':'CSV analyzed; not saved.'}`;
  }catch(e){$('error').textContent=(e.name==='AbortError'?'Request timed out. Check that the local server is running and retry.':e.message)+(data?' Your previous analysis is unchanged.':' Use Restore demo to retry.');$('error').hidden=false;$('status').textContent='';}
  finally{clearTimeout(timer);busy=false;$('savedRace').disabled=false;$('importButton').disabled=false;$('reset').disabled=false;$('export').disabled=!data;}
}
$('clean').onchange=renderChart;
document.querySelectorAll('input[name=depth]').forEach(input=>input.onchange=renderBrief);
$('tableDriver').onchange=renderLaps;
$('reset').onclick=()=>{if(!busy){$('savedRace').value='';load('/api/races/demo')}};
$('export').onclick=()=>{if(data)save('race-analysis.json',JSON.stringify(data,null,2),'application/json')};
$('importForm').onsubmit=async event=>{
  event.preventDefault();if(busy)return;
  const file=$('csvFile').files[0];if(!file)return;
  if(file.size>500000){$('error').textContent='File exceeds 500 KB. Export a smaller, single-race CSV.';$('error').hidden=false;return;}
  try{const csv=await file.text();await load('/api/races/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('raceTitle').value,csv})});}
  catch(e){$('error').textContent='Could not read that file. Choose a UTF-8 CSV and retry.';$('error').hidden=false;}
};
$('savedRace').onchange=()=>{if(!busy)load($('savedRace').value?'/api/library/races/'+encodeURIComponent($('savedRace').value):'/api/races/demo')};
async function initLibrary(){
  try{
    const response=await fetch('/api/library/sessions');if(!response.ok)throw Error('Library unavailable');
    const sessions=(await response.json()).filter(s=>s.race_records>0);
    $('savedRace').innerHTML='<option value="">Synthetic exercise</option>'+sessions.map(s=>`<option value="${esc(s.id)}">${esc(s.name)}</option>`).join('');
    const preferred=new URLSearchParams(location.search).get('session');
    if(preferred&&!sessions.some(s=>s.id===preferred))throw Error('Requested race is not in the saved library. Choose another session.');
    const id=preferred||sessions[0]?.id||'';$('savedRace').value=id;
    await load(id?'/api/library/races/'+encodeURIComponent(id):'/api/races/demo');
  }catch(e){$('error').textContent=e.message+' Use Restore demo or visit the session library.';$('error').hidden=false;}
}
initLibrary();
