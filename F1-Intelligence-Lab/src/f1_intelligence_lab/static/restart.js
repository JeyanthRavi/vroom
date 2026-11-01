const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export async function renderRestart(){
  if(document.querySelector('#restart-research'))return;
  const section=document.createElement('section');section.id='restart-research';
  section.innerHTML='<h2>10 / Restart-aware models</h2><div aria-live="polite">Loading 2025-only experiment…</div>';
  document.querySelector('main').append(section);
  const link=document.createElement('a');link.href='#restart-research';link.textContent='10 Restart models';document.querySelector('.section-nav').append(link);
  const box=section.querySelector('div');
  try{
    const response=await fetch('/api/ml/restart-research'),d=await response.json();
    if(!response.ok)throw Error(d.detail||'Experiment unavailable');
    if(d.status!=='ready'){box.textContent=d.message;return;}
    const names=['rolling_median','unmodified_sequence_boosting',d.tree_candidate,'robust_gru'];
    box.innerHTML=`<p>Trained on ${d.coverage.train.eligible_rows.toLocaleString()} examples from ${d.coverage.train.races} races in 2025 only. Tuning uses five separate 2025 validation races. 2026 was not loaded or scored in this experiment.</p><p>Long historical laps no longer become the next prediction’s reference time. The models retain long-lap indicators and known race-control transitions. Long target laps are still counted, not discarded.</p><p class="warning">Ordinary validation winner: ${esc(d.winner)}. Restart-aware models improve the synthetic interruption test but do not beat the unchanged boosting comparator on ordinary validation. Existing website predictions are unchanged. No claim of improved 2026 accuracy.</p><div class="table-scroll"><table><thead><tr><th>Model</th><th>Validation MAE (s)</th><th>Reused 2025 benchmark MAE (s)</th><th>Synthetic stress MAE (s)</th></tr></thead><tbody>${names.map(n=>`<tr><td>${esc(n)}</td><td>${d.scores.validation[n].race_macro_mae_s.toFixed(3)}</td><td>${d.scores.test[n].race_macro_mae_s.toFixed(3)}</td><td>${d.stress[n].race_macro_mae_s.toFixed(3)}</td></tr>`).join('')}</tbody></table></div><p class="muted">Stress test artificially multiplies the last historical lap by 10 while keeping targets fixed. It measures sensitivity, not real-world accuracy. All MAEs give races equal weight. ${esc(d.limitations)}</p>`;
  }catch(error){box.textContent=error.message;}
}
