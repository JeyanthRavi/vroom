// Saved cross-season evaluation only: no fitting, live forecasting or model promotion.
const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=v=>v==null?'—':Number(v).toFixed(3);
export async function renderCrossSeason(){
  if(document.querySelector('#cross-season'))return;
  const section=document.createElement('section');section.id='cross-season';
  section.innerHTML='<h2>09 / 2026 cross-season test</h2><div aria-live="polite">Loading frozen evaluation…</div>';
  document.querySelector('main').append(section);
  const link=document.createElement('a');link.href='#cross-season';link.textContent='09 2026 test';document.querySelector('.section-nav').append(link);
  const box=section.querySelector('div');
  try{
    const response=await fetch('/api/ml/cross-season'),d=await response.json();
    if(!response.ok)throw Error(d.detail||'Evaluation unavailable');
    if(d.status!=='ready'){box.textContent=d.message;return;}
    const selected=d.selected_before_2026,comparison=d.paired_vs_last_lap[selected];
    box.innerHTML=`<p>Frozen 2025-trained models, evaluated without retraining or model selection on 2026. All models share ${d.coverage.eligible_rows.toLocaleString()} eligible laps across ${d.coverage.races} verified races. ${d.coverage.original_rows-d.coverage.eligible_rows} incomplete/ambiguous histories were excluded; ${d.excluded_races.length} unverified races were not evaluated.</p><p class="warning">${esc(d.holdout_status)}. This is historical evaluation, not live prediction. Large errors and long laps remain in the results. The previously selected candidate remains ${esc(selected)}; no model is automatically promoted.</p><div class="table-scroll"><table><thead><tr><th>Model</th><th>Race MAE (s)</th><th>RMSE (s)</th><th>R²</th></tr></thead><tbody>${Object.entries(d.scores).map(([name,s])=>`<tr><td>${esc(name)}</td><td>${fmt(s.race_macro_mae_s)}</td><td>${fmt(s.rmse_s)}</td><td>${fmt(s.r2)}</td></tr>`).join('')}</tbody></table></div><p>${esc(selected)} minus last-lap baseline: ${fmt(comparison.mean_delta_s)} s race MAE; exploratory 95% paired race-bootstrap interval [${comparison.ci95_s.map(fmt).join(', ')}] s. Better in ${comparison.races_better}/${comparison.races} races. Negative favours the model. This is not uncertainty for an individual prediction.</p><details open><summary>Race-by-race generalization</summary><div class="table-scroll"><table><thead><tr><th>Circuit</th><th>Laps</th><th>Last lap MAE</th><th>Median MAE</th><th>Boosting MAE</th><th>GRU MAE</th></tr></thead><tbody>${d.races.map(r=>{const id=r.session_id;return `<tr><td><a href="?session=${encodeURIComponent(id)}#cross-season">${esc(r.circuit)}</a></td><td>${d.scores.last_lap.per_race[id].rows}</td>${['last_lap','rolling_median','boosting_sequence','gru_full'].map(n=>`<td>${fmt(d.scores[n].per_race[id].mae_s)}</td>`).join('')}</tr>`;}).join('')}</tbody></table></div></details><details><summary>Excluded races and coverage</summary><p>${esc(JSON.stringify(d.coverage.excluded))}</p>${d.excluded_races.map(r=>`<p>${esc(r.session_id)}: ${esc(r.blockers.join('; '))}</p>`).join('')}</details><p class="muted">${esc(d.limitations)} Bootstrap assumes exchangeable races and does not account for all temporal dependence. Version ${esc(d.version)}.</p>`;
  }catch(error){box.textContent=error.message;}
}
