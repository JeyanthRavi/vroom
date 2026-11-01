// Historical model explorer. No client-side fitting or substitute predictions.
import {renderCrossSeason} from './cross-season.js';
import {renderRestart} from './restart.js';
const escape=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let generation=0;
let experimentLoaded=false;
async function renderExperiment(){
  if(experimentLoaded)return;
  experimentLoaded=true;
  const section=document.createElement('section');section.id='ml-research';
  section.innerHTML='<h2>08 / ML × Deep learning lab</h2><div class="research-content" aria-live="polite">Loading experiment results…</div>';
  document.querySelector('main').append(section);
  const link=document.createElement('a');link.href='#ml-research';link.textContent='08 ML / DL research';document.querySelector('.section-nav').append(link);
  const box=section.querySelector('.research-content');
  try{
    const response=await fetch('/api/ml/experiment'),data=await response.json();
    if(!response.ok)throw Error(data.detail||'Experiment unavailable');
    if(data.status!=='ready'){box.textContent=data.message;return;}
    const n=v=>Number(v).toFixed(3);
    box.innerHTML=`<p>A PyTorch GRU reads the preceding 10 completed laps and predicts the next lap’s duration. Three seeds are averaged. Compare against simple baselines and gradient-boosted trees on exactly the same eligible laps.</p><p class="warning">Research benchmark across races—not a prediction for the selected race. The 2025 benchmark was previously inspected; it is not a pristine holdout. 2026 was unopened during this experiment; see the separate cross-season evaluation below. These scores are not directly comparable to the three-lap model above.</p><div class="stats">${Object.entries(data.coverage).map(([split,c])=>`<div class="stat"><b>${c.eligible_rows.toLocaleString()}</b><span>${escape(split)} examples · ${c.races} races</span></div>`).join('')}</div><p>Validation-selected candidate: <strong>${escape(data.winner)}</strong>. The model serving predictions above is unchanged.</p><div class="table-scroll"><table><thead><tr><th>Model</th><th>Validation MAE (s)</th><th>Benchmark MAE (s)</th><th>Benchmark RMSE (s)</th><th>Benchmark R²</th><th>Individual-seed validation MAE (s)</th></tr></thead><tbody>${data.models.map(m=>`<tr><td>${escape(m.name)}</td><td>${n(m.validation.race_macro_mae_s)}</td><td>${n(m.benchmark.race_macro_mae_s)}</td><td>${n(m.benchmark.rmse_s)}</td><td>${n(m.benchmark.r2)}</td><td>${m.seed_validation_mae.map(n).join(' / ')||'—'}</td></tr>`).join('')}</tbody></table></div><p class="muted">MAE gives each race equal weight; lower is better. RMSE and R² pool eligible laps. Tyre/control ablations remove those inputs from both the sequence and context; they do not establish causation. Checkpoint selection uses validation only. Version ${escape(data.version)}.</p>`;
  }catch(error){box.textContent=error.message;}
}
function shell(){
  if(document.querySelector('#ml'))return;
  const section=document.createElement('section');section.id='ml';
  section.innerHTML='<h2>07 / Next-lap model</h2><p class="muted">Historical predictions at lap start using the preceding three completed laps. Actual times are shown afterwards for comparison—not provided to the model. This is not a live forecast or pit-strategy recommendation.</p><div class="ml-content" aria-live="polite"></div>';
  document.querySelector('main').append(section);
  const link=document.createElement('a');link.href='#ml';link.textContent='07 ML predictions';document.querySelector('.section-nav').append(link);
}
export async function renderML(sid){
  let replay=document.querySelector('#model-replay-link');
  if(!replay){replay=document.createElement('a');replay.id='model-replay-link';replay.textContent='11 ML / DL race replay ↗';document.querySelector('.section-nav').append(replay);}
  replay.href='/model-demo/?session='+encodeURIComponent(sid);
  shell();const token=++generation,box=document.querySelector('.ml-content');
  renderExperiment();
  renderCrossSeason();
  renderRestart();
  box.textContent='Loading verified model predictions…';
  try{
    const response=await fetch('/api/ml/races/'+encodeURIComponent(sid));const data=await response.json();
    if(token!==generation||document.querySelector('#race').value!==sid)return;
    if(!response.ok)throw Error(data.detail||'Prediction service unavailable');
    if(data.status!=='ready'){
      box.innerHTML=`<p class="empty">${escape(data.message)}</p>`;
      const eligible=(data.available_sessions||[]).filter(s=>s.split==='test');
      if(eligible.length)box.innerHTML+='<p>Explore a held-out race: '+eligible.map(s=>`<a class="source" href="?session=${encodeURIComponent(s.session_id)}#ml">${escape(s.session_id)}</a>`).join(' · ')+'</p>';
      return;
    }
    const drivers=[...new Set(data.rows.map(r=>r.driver))].sort((a,b)=>Number(a)-Number(b));
    box.innerHTML=`<p class="warning">${escape(data.message)}</p><p class="muted">Model: ${escape(data.model)} · version ${escape(data.version)} · ${data.rows.length} eligible lap examples. Omitted laps have no verified eligible history; gaps are not interpolated.</p><label for="mlDriver">Driver number</label><select id="mlDriver">${drivers.map(d=>`<option>${escape(d)}</option>`).join('')}</select><div id="mlSummary" class="stats"></div><p>● Actual <span style="color:#72dce8">◆ Model prediction</span></p><div id="mlChart"></div><details><summary>Exact predictions and errors</summary><div id="mlTable" class="table-scroll"></div></details><p class="muted">Model was fitted on 15 races and evaluated on three held-out test races. Historical event timestamps do not prove live feed availability. Race-wide MAE is not a confidence interval; individual errors can be much larger. 2026 is handled by the separate cross-season evaluation below.</p>`;
    function draw(){
      const rows=data.rows.filter(r=>r.driver===document.querySelector('#mlDriver').value).sort((a,b)=>a.lap-b.lap);
      const mae=rows.reduce((s,r)=>s+r.absolute_error_s,0)/rows.length;
      const baseline=rows.reduce((s,r)=>s+Math.abs(r.baseline_s-r.actual_s),0)/rows.length;
      document.querySelector('#mlSummary').innerHTML=[[rows.length,'eligible laps'],[mae.toFixed(3)+' s','driver MAE'],[baseline.toFixed(3)+' s','baseline MAE'],[data.split,'dataset partition']].map(([n,t])=>`<div class="stat"><b>${escape(n)}</b><span>${t}</span></div>`).join('');
      const values=rows.flatMap(r=>[r.actual_s,r.predicted_s]),lo=Math.min(...values)-1,hi=Math.max(...values)+1,last=Math.max(...rows.map(r=>r.lap));
      const x=lap=>60+(lap-1)/Math.max(last-1,1)*810,y=v=>200-(v-lo)/(hi-lo)*175;
      document.querySelector('#mlChart').innerHTML=`<svg viewBox="0 0 900 240" role="img" aria-label="Actual versus predicted lap times. Exact values in the table below."><path d="M60 20V200H880" fill="none" stroke="#777"/><text x="0" y="25" fill="#bbb" font-size="12">${hi.toFixed(1)} s</text><text x="0" y="200" fill="#bbb" font-size="12">${lo.toFixed(1)} s</text><text x="60" y="225" fill="#bbb">Lap 1</text><text x="800" y="225" fill="#bbb">Lap ${last}</text>${rows.map(r=>`<circle cx="${x(r.lap)}" cy="${y(r.actual_s)}" r="3" fill="#fff"><title>Lap ${r.lap}: actual ${r.actual_s.toFixed(3)} s</title></circle><path d="M${x(r.lap)},${y(r.predicted_s)-4}l4,4 -4,4 -4,-4Z" fill="#72dce8"><title>Lap ${r.lap}: predicted ${r.predicted_s.toFixed(3)} s</title></path>`).join('')}</svg>`;
      document.querySelector('#mlTable').innerHTML='<table><thead><tr>'+['Lap','Predicted (s)','Actual (s)','Absolute error (s)','Baseline (s)','State at cutoff'].map(t=>`<th>${t}</th>`).join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+[r.lap,r.predicted_s.toFixed(3),r.actual_s.toFixed(3),r.absolute_error_s.toFixed(3),r.baseline_s.toFixed(3),r.control_state].map(v=>`<td>${escape(v)}</td>`).join('')+'</tr>').join('')+'</tbody></table>';
    }
    document.querySelector('#mlDriver').addEventListener('change',draw);draw();
  }catch(error){if(token===generation&&document.querySelector('#race').value===sid)box.textContent=error.message;}
}
