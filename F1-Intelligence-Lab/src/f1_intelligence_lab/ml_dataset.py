"""Fail-closed loader for audited datasets; never expose metadata as model inputs."""
import csv
import json
import math
from pathlib import Path
from .ml_prep import FEATURES, META, LABEL, digest, dt, split_for

CATEGORICAL={'circuit','previous_compound','control_state_at_cutoff'}

def load_split(directory, split, *, allow_future_evaluation=False):
    if split not in {'train','validation','test'} and not (split=='future_holdout' and allow_future_evaluation):
        raise ValueError('Use train, validation or test. Future holdout is reserved for later evaluation.')
    directory=Path(directory)
    manifest=json.loads((directory/'manifest.json').read_text())
    for name in ['audit.json','feature_contract.json',split+'.csv']:
        if manifest.get(name)!=digest((directory/name).read_bytes()): raise ValueError('Dataset checksum mismatch: '+name)
    audit=json.loads((directory/'audit.json').read_text())
    if audit['training_gate']!='ready_for_baseline': raise ValueError('Audit has not passed the training gate')
    contract=json.loads((directory/'feature_contract.json').read_text())
    if contract['features']!=FEATURES or contract['target']!=LABEL: raise ValueError('Feature contract mismatch')
    allowed={s['session_id'] for s in audit['session_reports'] if s['verified_for_prep'] and s['split']==split}
    with (directory/(split+'.csv')).open() as file:
        reader=csv.DictReader(file)
        if reader.fieldnames!=META+FEATURES+[LABEL]: raise ValueError('Unexpected dataset columns')
        rows=list(reader)
    if not rows or len(rows)!=audit['split_rows'][split]: raise ValueError('Dataset row count mismatch')
    X=[]; y=[]; metadata=[]; seen=set()
    for row in rows:
        if row['session_id'] not in allowed or row['session_verified']!='1' or row['split']!=split or split_for(row['race_start'])!=split:
            raise ValueError('Unverified or incorrectly partitioned session')
        if row['row_id'] in seen: raise ValueError('Duplicate prediction row')
        seen.add(row['row_id'])
        if dt(row['latest_feature_at'])>dt(row['prediction_at']): raise ValueError('Future feature timestamp')
        features={k:row[k] if k in CATEGORICAL else float(row[k]) for k in FEATURES}
        label=float(row[LABEL])
        if not all(math.isfinite(v) for v in [label]+[v for k,v in features.items() if k not in CATEGORICAL]):
            raise ValueError('Non-finite model input')
        X.append(features); y.append(label); metadata.append({k:row[k] for k in META})
    return X,y,metadata
