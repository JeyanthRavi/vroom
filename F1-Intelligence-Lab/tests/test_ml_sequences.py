from copy import deepcopy
from datetime import datetime,timedelta,timezone
import pytest
from f1_intelligence_lab.ml_sequences import history_for,build_split,ablate

START=datetime(2025,1,1,tzinfo=timezone.utc)


def history():
    return [{'driver_number':44,'lap_number':i,'lap_duration':90.,'is_pit_out_lap':False,
             '_start':START+timedelta(seconds=(i-1)*90),'_end':START+timedelta(seconds=i*90)} for i in range(1,13)]


STINTS=[{'driver_number':44,'lap_start':1,'lap_end':99,'compound':'MEDIUM','tyre_age_at_start':0}]


def test_ten_laps_are_shifted_and_exclude_future():
    rows=history(); cutoff=START+timedelta(seconds=900)
    seq,reason=history_for(rows,44,11,cutoff,STINTS,[],90.)
    assert reason is None and len(seq)==10
    assert [s['lap_number'] for s in seq]==list(range(1,11))
    changed=deepcopy(rows)
    for r in changed[10:]: r['lap_duration']=1234.
    future=STINTS+[{'driver_number':44,'lap_start':11,'compound':'WET','tyre_age_at_start':0}]
    future[0]=dict(future[0],lap_end=1000)
    after,_=history_for(changed,44,11,cutoff,future,[{'date':(cutoff+timedelta(seconds=1)).isoformat(),'flag':'RED'}],90.)
    assert seq==after
    assert seq[-1]['tyre_age']==10


def test_gap_late_end_and_ambiguous_stints_fail_closed():
    rows=history(); cutoff=START+timedelta(seconds=900)
    assert history_for(rows[1:],44,11,cutoff,STINTS,[],90.)[1]=='missing_contiguous_history'
    rows[9]['_end']+=timedelta(milliseconds=1)
    assert history_for(rows,44,11,cutoff,STINTS,[],90.)[1]=='history_after_cutoff'
    assert history_for(history(),44,11,cutoff,STINTS+STINTS,[],90.)[1]=='ambiguous_tyre_history'


def test_ablation_covers_context_and_sequence():
    fields={'compound':'SOFT','previous_compound':'SOFT','tyre_age':1,'previous_tyre_age':1,
            'stint_lap':1,'previous_stint_lap':1,'control_state':'RED','control_state_at_cutoff':'RED','pace_delta_s':0.}
    assert set(ablate(fields,'no_tyre'))=={'control_state','control_state_at_cutoff','pace_delta_s'}
    assert not {'control_state','control_state_at_cutoff'}&set(ablate(fields,'no_control'))


def test_future_holdout_refused_before_files_read(tmp_path):
    with pytest.raises(ValueError,match='reserved'):
        build_split(tmp_path,tmp_path,'future_holdout')
