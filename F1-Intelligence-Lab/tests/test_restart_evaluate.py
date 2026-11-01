import json

import pytest

pytest.importorskip('torch')
from f1_intelligence_lab.ml_prep import digest
from f1_intelligence_lab.restart_evaluate import masks, resumption_events, sliced_score, verify


def sample():
    return {'x':[{'lag_1_s':90.,'control_state_at_cutoff':'GREEN'}],
        'y':[2000.], 'meta':[{'session_id':'test'}],
        'sequences':[[{'pace_delta_s':0.,'control_state':'GREEN'} for _ in range(10)]]}


def test_target_long_does_not_imply_previous_interruption():
    d=sample();m=masks(d,2.)
    assert m['observed_target_over_180s'].tolist()==[True]
    assert not m['previous_lap_over_frozen_ratio'][0]
    assert not m['recent_known_control_restart'][0]


def test_recent_history_and_restart_slices():
    d=sample();d['y']=[90.]
    d['sequences'][0][-2].update(pace_delta_s=900.,control_state='RED')
    m=masks(d,2.)
    assert m['within_three_laps_after_long_history'][0]
    assert not m['previous_lap_over_frozen_ratio'][0]
    assert m['recent_known_control_restart'][0]
    assert not m['known_control_restart_at_cutoff'][0]
    assert not m['ordinary_target_no_recent_long_history'][0]
    d['sequences'][0][-1]['control_state']='RED'
    assert masks(d,2.)['known_control_restart_at_cutoff'][0]


def test_empty_slice_is_not_zero_error():
    assert sliced_score(sample(),[90.],[False])=={'rows':0,'races':0}


def test_checksum_fail_closed(tmp_path):
    (tmp_path/'model').write_bytes(b'original')
    (tmp_path/'artifact_hashes.json').write_text(json.dumps({'model':digest(b'original')}))
    assert verify(tmp_path,['model'])['model']==digest(b'original')
    (tmp_path/'model').write_bytes(b'changed')
    with pytest.raises(ValueError,match='integrity'):verify(tmp_path,['model'])


def test_resumption_requires_suspension_then_actual_start():
    messages=['SESSION STARTED','INCIDENT NOTED - RED FLAG INFRINGEMENT',
              'SESSION STARTED','RED FLAG - RACE SUSPENDED','RACE WILL RESUME AT 17:12',
              'SESSION STARTED','SESSION STARTED']
    events=[{'date':f'2026-06-07T15:00:0{i}+00:00','message':m} for i,m in enumerate(messages)]
    assert resumption_events(events)==[events[5]]
