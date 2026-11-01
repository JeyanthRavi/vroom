const $=id=>document.getElementById(id);
const names={last_lap:'Last lap',rolling_median:'Rolling median',boosting_2025:'Boosting · corrected states',restart_boosting:'Restart-aware boosting',restart_gru:'Restart-aware GRU ensemble',original_boosting:'Original boosting',original_gru:'Original GRU'};
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=v=>v===null||v===undefined?'—':Number(v).toFixed(3);
const option=(value,text)=>{const o=document.createElement('option');o.value=value;o.textContent=text;return o;};
const cohortText=split=>({train:'Training race: in-sample, not independent accuracy.',validation:'2025 validation: used for model selection.',test:'Reused 2025 benchmark: not a pristine holdout.',future_holdout:'Evaluated on previously examined 2026 races; not an independent holdout.'}[split]||split);
const lineChart=(rows,xKey,yKey,color)=>{if(!rows.length)return '';const values=rows.map(row=>Number(row[yKey])),lo=Math.min(...values),hi=Math.max(...values),span=Math.max(.001,hi-lo),x=index=>35+index/Math.max(1,rows.length-1)*245,y=value=>175-(value-lo)/span*135;return `<line x1="35" y1="175" x2="280" y2="175" stroke="#738198"/><line x1="35" y1="40" x2="35" y2="175" stroke="#738198"/><polyline fill="none" stroke="${color}" stroke-width="3" points="${rows.map((row,index)=>`${x(index)},${y(Number(row[yKey]))}`).join(' ')}"/><text x="35" y="205" fill="#bbc3ce" font-size="12">${esc(rows[0][xKey])}</text><text x="235" y="205" fill="#bbc3ce" font-size="12">${esc(rows.at(-1)[xKey])}</text>`;};
function renderResearch(research){
 const reliability=research.hazard['1'].reliability;
 $('hazard-summary').textContent=`Fixture H=1 Brier ${fmt(research.hazard['1'].brier)}; base-rate Brier ${fmt(research.hazard['1'].baseline_brier)}. Baseline shown beside model; lower is better.`;
 $('hazard-chart').innerHTML='<line x1="35" y1="175" x2="280" y2="40" stroke="#738198" stroke-dasharray="5 5"/>'+lineChart(reliability,'mean_probability','observed_rate','#5eead4');
 $('hazard-alt').textContent='Fixture-only reliability diagram: observed synthetic event frequency plotted across increasing predicted-probability bins; diagonal is ideal calibration.';
 const intervals=Object.entries(research.intervals);
 $('interval-summary').textContent='Fixture-only empirical coverage is shown next to nominal coverage and mean width; these are not calibrated Formula 1 intervals.';
 $('interval-table').innerHTML=`<table><thead><tr><th>Method</th><th>Nominal</th><th>Coverage</th><th>Width (s)</th></tr></thead><tbody>${intervals.map(([name,row])=>`<tr><td>${esc(name)}</td><td>${fmt(row.nominal_coverage)}</td><td>${fmt(row.coverage)}</td><td>${fmt(row.mean_width_s)}</td></tr>`).join('')}</tbody></table>`;
 const drift=research.drift.rolling_origin;
 $('drift-summary').textContent='Rolling-median error on deterministic fixture races. This demonstrates the timeline UI; it is not evidence of real-season drift.';
 $('drift-chart').innerHTML=lineChart(drift,'race_id','rolling_median_5_mae_s','#ffcc80');
 $('drift-alt').textContent='Fixture-only line chart of rolling-median five-lap MAE in seconds across synthetic race order.';
}

try{
 const [dataResponse,metadataResponse,researchResponse]=await Promise.all([fetch('data.json'),fetch('export-metadata.json'),fetch('research.json')]);
 if(!dataResponse.ok||!metadataResponse.ok||!researchResponse.ok)throw Error('Replay package unavailable');
 const data=await dataResponse.json(),metadata=await metadataResponse.json(),research=await researchResponse.json();
 const mode=metadata.export_mode;
 $('mode').textContent=mode==='aggregate'?'Aggregate export · no lap-level observations':mode==='legacy_full'?'Legacy full export · lap-level data included':'Full export · lap-level data included';
 $('mode').style.background=mode==='aggregate'?'#155e4b':'#7c2d12';
 $('limits').textContent=data.limitations;
 $('status').textContent=`Historical replay · model ${data.model_version} · state parser v${data.control_version}`;
 $('footer-build').textContent=`Mode: ${mode}; version: ${metadata.version}; commit: ${metadata.git_commit.slice(0,12)}.`;
 renderResearch(research);
 $('comparison').innerHTML=Object.entries(data.regression).map(([n,s])=>`<tr><td>${esc(names[n]||n)}</td><td>${fmt(s.race_macro_mae_s)}</td><td>${fmt(s.rmse_s)}</td><td>${fmt(s.r2)}</td></tr>`).join('');
 if(mode==='aggregate'){
  if(data.schema!==2||!Array.isArray(data.races))throw Error('Unsupported aggregate replay format');
  $('aggregate').hidden=false;
  data.races.sort((a,b)=>b.date.localeCompare(a.date)).forEach(s=>$('aggregate-session').append(option(s.id,`${s.date.slice(0,4)} · ${s.circuit}`)));
  const renderAggregate=()=>{const race=data.races.find(s=>s.id===$('aggregate-session').value);$('aggregate-cohort').textContent=cohortText(race.split);$('aggregate-rows').innerHTML=Object.entries(race.summary).map(([model,s])=>`<tr><td>${esc(names[model]||model)}</td><td>${s.eligible_laps}</td><td>${fmt(s.mae_s)}</td><td>${fmt(s.median_ae_s)}</td></tr>`).join('');};
  $('aggregate-session').addEventListener('change',renderAggregate);renderAggregate();
 }else{
  if(data.schema!==1||!Array.isArray(data.sessions))throw Error('Unsupported full replay format');
  $('full').hidden=false;data.sessions.sort((a,b)=>b.date.localeCompare(a.date)).forEach(s=>$('session').append(option(s.id,`${s.date.slice(0,4)} · ${s.circuit}`)));data.models.forEach(m=>$('model').append(option(m,names[m]||m)));$('model').value=data.selected_on_2025;
  const requested=new URLSearchParams(location.search).get('session');if(data.sessions.some(s=>s.id===requested))$('session').value=requested;
  function session(){return data.sessions.find(s=>s.id===$('session').value);}
  function raceChanged(){const s=session();$('driver').replaceChildren();[...new Set(s.rows.map(r=>r.driver))].sort((a,b)=>Number(a)-Number(b)).forEach(d=>$('driver').append(option(d,`Car ${d}`)));render();}
  function render(){const s=session(),model=$('model').value,rows=s.rows.filter(r=>r.driver===$('driver').value).sort((a,b)=>a.lap-b.lap);$('cohort').textContent=cohortText(s.split);const mae=key=>rows.reduce((a,r)=>a+Math.abs(r.actual-r.predictions[key]),0)/rows.length;$('stats').innerHTML=`<div><b>${rows.length}</b><span>eligible laps</span></div><div><b>${fmt(mae(model))}s</b><span>driver MAE</span></div><div><b>${fmt(mae('rolling_median'))}s</b><span>baseline MAE</span></div>`;const all=rows.flatMap(r=>[r.actual,r.predictions[model],r.predictions.rolling_median]);const lo=Math.max(0,Math.min(...all)-5),hi=Math.max(...all)+5;const first=rows[0].lap,last=rows.at(-1).lap,x=l=>65+(l-first)/Math.max(1,last-first)*910,y=v=>290-(v-lo)/(hi-lo)*260;let svg='';for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;svg+=`<line x1="65" x2="975" y1="${y(v)}" y2="${y(v)}" stroke="#343c49"/><text x="4" y="${y(v)+4}" fill="#bbc3ce" font-size="13">${v.toFixed(1)}s</text>`;}for(const [key,color,dash] of [['actual','#fff',''],[model,'#ff665b',''],['rolling_median','#5eead4','6 4']])svg+=`<polyline fill="none" stroke="${color}" stroke-width="2" stroke-dasharray="${dash}" points="${rows.map(r=>`${x(r.lap)},${y(key==='actual'?r.actual:r.predictions[key])}`).join(' ')}"/>`;svg+=`<text x="65" y="325" fill="#bbc3ce">Lap ${first}</text><text x="900" y="325" fill="#bbc3ce">Lap ${last}</text>`;$('chart').innerHTML=svg;$('rows').innerHTML=rows.map(r=>`<tr><td>${r.lap}</td><td>${esc(r.state)}</td><td>${fmt(r.actual)}</td><td>${fmt(r.predictions[model])}</td><td>${fmt(r.predictions.rolling_median)}</td><td>${fmt(Math.abs(r.actual-r.predictions[model]))}</td></tr>`).join('');}
  $('session').addEventListener('change',raceChanged);$('driver').addEventListener('change',render);$('model').addEventListener('change',render);raceChanged();
 }
}catch(e){$('status').textContent=`Replay unavailable: ${e.message}. No substitute predictions are shown.`;}
