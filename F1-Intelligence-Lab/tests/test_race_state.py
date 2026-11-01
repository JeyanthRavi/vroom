from f1_intelligence_lab.ml_prep import dt
from f1_intelligence_lab.race_state import state_at


def event(n,message='',flag=None,scope=None,sector=None):
    return {'date': f'2025-01-01T00:00:{n:02d}Z','message': message,'flag': flag,'scope': scope,'sector': sector}

def test_local_flags_do_not_end_neutralisation():
    events=[event(1,'SAFETY CAR DEPLOYED'),event(2,flag='YELLOW',scope='Sector',sector=2),event(3,flag='CLEAR',scope='Sector',sector=2)]
    assert state_at(events,dt(events[1]['date']))['local_yellow_sectors']==1
    state=state_at(events,dt(events[2]['date']))
    assert state['state']=='SC' and state['local_yellow_sectors']==0

def test_text_red_actual_resumption_not_pit_exit():
    events=[event(1,'RED FLAG - RACE SUSPENDED'),event(2,'RACE WILL RESUME AT 17:12'),event(3,'GREEN LIGHT - PIT EXIT OPEN','GREEN','Track'),event(4,'SESSION STARTED'),event(5,'GREEN FLAG','GREEN','Track')]
    assert state_at(events,dt(events[2]['date']))['state']=='RED'
    assert state_at(events,dt(events[3]['date']))['state']=='RESTART'
    assert state_at(events,dt(events[4]['date']))['state']=='GREEN'

def test_future_events_and_incident_mentions_ignored():
    events=[event(1,'SESSION STARTED'),event(2,'INCIDENT NOTED - RED FLAG INFRINGEMENT'),event(3,'SAFETY CAR DEPLOYED')]
    assert state_at(events,dt(events[1]['date']))['state']=='GREEN'

def test_announced_end_keeps_vsc_until_explicit_green():
    events=[event(1,'VIRTUAL SAFETY CAR DEPLOYED'),event(2,'VIRTUAL SAFETY CAR ENDING'),event(3,'GREEN FLAG','GREEN','Track')]
    assert state_at(events,dt(events[1]['date']))['state']=='VSC'
    assert state_at(events,dt(events[2]['date']))['restart_count']==1

def test_red_flag_then_session_started_is_restart():
    events=[event(1,'RED FLAG - RACE SUSPENDED'),event(2,'SESSION STARTED')]
    assert state_at(events,dt(events[1]['date']))['state']=='RESTART'

def test_pit_exit_green_does_not_set_green():
    events=[event(1,'RED FLAG - RACE SUSPENDED'),event(2,'GREEN LIGHT - PIT EXIT OPEN','GREEN','Track')]
    assert state_at(events,dt(events[1]['date']))['state']=='RED'

def test_safety_car_in_this_lap_does_not_end_neutralisation():
    events=[event(1,'SAFETY CAR DEPLOYED'),event(2,'SAFETY CAR IN THIS LAP')]
    assert state_at(events,dt(events[1]['date']))['state']=='SC'

def test_unordered_events_are_sorted_and_future_cutoff_is_respected():
    events=[event(3,'SAFETY CAR DEPLOYED'),event(1,'SESSION STARTED'),event(2,'GREEN FLAG','GREEN','Track')]
    assert state_at(events,dt(event(2)['date']))['state']=='GREEN'
    assert state_at(events,dt(event(3)['date']))['state']=='SC'
