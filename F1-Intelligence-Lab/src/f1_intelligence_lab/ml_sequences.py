"""Ten-lap histories reconstructed from checksum-verified 2025 source caches."""
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse
from .ml_dataset import load_split
from .ml_prep import COMPOUNDS, control_at, digest, dt, integer, validate_laps

WINDOW = 10
STEP_FEATURES = ['pace_delta_s','lap_number','compound','tyre_age','stint_lap','pit_out','control_state']


def history_for(valid, car, lap, cutoff, stints, control, anchor):
    lookup={r['lap_number']:r for r in valid if r['driver_number']==car}
    history=[lookup.get(n) for n in range(lap-WINDOW,lap)]
    if any(r is None for r in history):
        return None,'missing_contiguous_history'
    if any(r['_end']>cutoff for r in history):
        return None,'history_after_cutoff'
    if history[-1]['lap_duration']!=anchor:
        raise ValueError('Last-lap anchor differs from audited feature')
    events=sorted(control,key=lambda e:dt(e['date']))
    sequence=[]
    for r in history:
        candidates=[s for s in stints if s.get('driver_number')==car and integer(s.get('lap_start')) and s['lap_start']<=r['lap_number']]
        candidates.sort(key=lambda s:s['lap_start'])
        s=candidates[-1] if candidates else None
        if not s or s.get('compound') not in COMPOUNDS or not integer(s.get('tyre_age_at_start')) or s['tyre_age_at_start']<0:
            return None,'missing_tyre_history'
        if sum(t['lap_start']==s['lap_start'] for t in candidates)!=1:
            return None,'ambiguous_tyre_history'
        age=r['lap_number']-s['lap_start']+1
        sequence.append({'pace_delta_s':r['lap_duration']-anchor,'lap_number':r['lap_number'],
            'compound':s['compound'],'tyre_age':s['tyre_age_at_start']+age,'stint_lap':age,
            'pit_out':int(r['is_pit_out_lap']), 'control_state':control_at(events,r['_start'])})
    return sequence,None


def build_split(dataset, source_root, split, *, allow_future_evaluation=False, control_version=1):
    # load_split refuses future_holdout before any source-cache read.
    if control_version not in {1,2}:raise ValueError('Unknown control version')
    x,y,meta=load_split(dataset,split,allow_future_evaluation=allow_future_evaluation)
    audit=json.loads((Path(dataset)/'audit.json').read_text())
    reports={s['session_id']:s for s in audit['session_reports']}
    kept_x=[]; kept_y=[]; kept_meta=[]; sequences=[]; sources={}; excluded=Counter()
    for sid in sorted({m['session_id'] for m in meta}):
        report=reports[sid]
        raw={}
        for source in report['sources']:
            endpoint=urlparse(source['url']).path.rsplit('/',1)[-1]
            if endpoint not in {'sessions','laps','drivers','session_result','stints','race_control'}:
                continue
            filename=digest(source['url'].encode())+'.json'
            content=(Path(source_root)/'openf1-cache'/filename).read_bytes()
            if digest(content)!=source['sha256']:
                raise ValueError('Source cache changed since audit: '+endpoint)
            raw[endpoint]=json.loads(content)
            sources[source['url']]=source['sha256']
        key=int(sid.split('-')[1])
        session=next(s for s in raw['sessions'] if s['session_key']==key)
        if session['year']>=2026 and not (allow_future_evaluation and split=='future_holdout' and session['year']==2026):
            raise ValueError('Future season is reserved')
        valid,_=validate_laps(raw['laps'],session,{d['driver_number'] for d in raw['drivers']},dt(audit['created_at']),raw['session_result'])
        targets={(r['driver_number'],r['lap_number']):r for r in valid}
        for features,label,m in zip(x,y,meta):
            if m['session_id']!=sid: continue
            car,lap=int(m['driver_number']),int(features['lap_number'])
            target=targets.get((car,lap))
            if target is None or target['lap_duration']!=label or target['_start']!=dt(m['prediction_at']):
                raise ValueError('Target differs from frozen dataset')
            seq,reason=history_for(valid,car,lap,dt(m['prediction_at']),raw['stints'],raw['race_control'],features['lag_1_s'])
            if reason: excluded[reason]+=1; continue
            if control_version==2:
                from .race_state import state_at
                features=dict(features)
                current=state_at(raw['race_control'],dt(m['prediction_at']))
                features['control_state_at_cutoff']=current['state']
                for step in seq:
                    historical=targets[(car,step['lap_number'])]
                    state=state_at(raw['race_control'],historical['_start'])
                    step.update(control_state=state['state'],local_yellow_sectors=state['local_yellow_sectors'],
                                restart_count=state['restart_count'],seconds_since_restart=state['seconds_since_restart'])
                    step.update(cutoff_restart_count=current['restart_count'],
                                cutoff_seconds_since_restart=current['seconds_since_restart'],
                                cutoff_local_yellow_sectors=current['local_yellow_sectors'])
            sequences.append(seq); kept_x.append(features); kept_y.append(label); kept_meta.append(m)
    if not sequences: raise ValueError('No eligible sequences')
    return {'x':kept_x,'y':kept_y,'meta':kept_meta,'sequences':sequences,
            'coverage':{'original_rows':len(x),'eligible_rows':len(kept_x),'excluded':dict(excluded),
                        'races':len({m['session_id'] for m in kept_meta})}, 'sources':sources}


def ablate(example, variant):
    if variant not in {'full','no_tyre','no_control'}: raise ValueError('Unknown ablation')
    drop={'no_tyre':{'compound','tyre_age','stint_lap','previous_compound','previous_tyre_age','previous_stint_lap'},
          'no_control':{'control_state','control_state_at_cutoff'},'full':set()}[variant]
    return {k:v for k,v in example.items() if k not in drop}


def flattened(data, variant='full'):
    return [dict(ablate(x,variant), **{f'h{j}_{k}':v for j,step in enumerate(seq) for k,v in ablate(step,variant).items()})
            for x,seq in zip(data['x'],data['sequences'])]
