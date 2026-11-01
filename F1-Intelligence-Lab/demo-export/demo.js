const $=id=>document.getElementById(id);
const names={last_lap:'Last lap',rolling_median:'Rolling median',boosting_2025:'Boosting · corrected states',restart_boosting:'Restart-aware boosting',restart_gru:'Restart-aware GRU ensemble',original_boosting:'Original boosting',original_gru:'Original GRU'};
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=v=>Number(v).toFixed(3);
try{
 const response=await fetch('data.json');if(!response.ok)throw Error('Replay package unavailable');
 const data=await response.json();
 if(data.schema!==1)throw Error('Unsupported replay format');
 const option=(value,text)=>{const o=document.createElement('option');o.value=value;o.textContent=text;return o;};
 data.sessions.sort((a,b)=>b.date.localeCompare(a.date)).forEach(s=>$('session').append(option(s.id,`${s.date.slice(0,4)} · ${s.circuit}`)));
 data.models.forEach(m=>$('model').append(option(m,names[m]||m)));$('model').value=data.selected_on_2025;
 const requested=new URLSearchParams(location.search).get('session');if(data.sessions.some(s=>s.id===requested))$('session').value=requested;
 $('limits').textContent=data.limitations;
 $('status').textContent=`Historical replay · model ${data.model_version} · state parser v${data.control_version} · ${data.sessions.length} races`;
 $('comparison').innerHTML=Object.entries(data.regression).map(([n,s])=>`<tr><td>${esc(names[n]||n)}</td><td>${fmt(s.race_macro_mae_s)}</td><td>${fmt(s.rmse_s)}</td><td>${fmt(s.r2)}</td></tr>`).join('');
 function session(){return data.sessions.find(s=>s.id===$('session').value);}
 function raceChanged(){const s=session();$('driver').replaceChildren();[...new Set(s.rows.map(r=>r.driver))].sort((a,b)=>Number(a)-Number(b)).forEach(d=>$('driver').append(option(d,`Car ${d}`)));render();}
 function render(){
  const s=session(),model=$('model').value,rows=s.rows.filter(r=>r.driver===$('driver').value).sort((a,b)=>a.lap-b.lap);
  $('cohort').textContent=({train:'Training race: in-sample, not independent accuracy.',validation:'2025 validation: used for model selection.',test:'Reused 2025 benchmark: not a pristine holdout.',future_holdout:'2026 regression: previously examined, never used for this training or tuning.'}[s.split]);
  const mae=key=>rows.reduce((a,r)=>a+Math.abs(r.actual-r.predictions[key]),0)/rows.length;
  $('stats').innerHTML=`<div><b>${rows.length}</b><span>eligible laps</span></div><div><b>${fmt(mae(model))}s</b><span>driver MAE</span></div><div><b>${fmt(mae('rolling_median'))}s</b><span>baseline MAE</span></div>`;
  const all=rows.flatMap(r=>[r.actual,r.predictions[model],r.predictions.rolling_median]);const lo=Math.max(0,Math.min(...all)-5),hi=Math.max(...all)+5;
  const first=rows[0].lap,last=rows.at(-1).lap,x=l=>65+(l-first)/Math.max(1,last-first)*910,y=v=>290-(v-lo)/(hi-lo)*260;
  let svg='';for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;svg+=`<line x1="65" x2="975" y1="${y(v)}" y2="${y(v)}" stroke="#343c49"/><text x="4" y="${y(v)+4}" fill="#bbc3ce" font-size="13">${v.toFixed(1)}s</text>`;}
  for(const [key,color,dash] of [['actual','#fff',''],[model,'#ff665b',''],['rolling_median','#5eead4','6 4']])svg+=`<polyline fill="none" stroke="${color}" stroke-width="2" stroke-dasharray="${dash}" points="${rows.map(r=>`${x(r.lap)},${y(key==='actual'?r.actual:r.predictions[key])}`).join(' ')}"/>`;
  svg+=`<text x="65" y="325" fill="#bbc3ce">Lap ${first}</text><text x="900" y="325" fill="#bbc3ce">Lap ${last}</text>`;$('chart').innerHTML=svg;
  $('rows').innerHTML=rows.map(r=>`<tr><td>${r.lap}</td><td>${esc(r.state)}</td><td>${fmt(r.actual)}</td><td>${fmt(r.predictions[model])}</td><td>${fmt(r.predictions.rolling_median)}</td><td>${fmt(Math.abs(r.actual-r.predictions[model]))}</td></tr>`).join('');
 }
 $('session').addEventListener('change',raceChanged);$('driver').addEventListener('change',render);$('model').addEventListener('change',render);raceChanged();
}catch(e){$('status').textContent=`Replay unavailable: ${e.message}. No substitute predictions are shown.`;}
