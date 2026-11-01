"""Version 2 event-time state: session neutralisation and local flags are separate."""
from .ml_prep import dt

VERSION=2


def state_at(events,cutoff):
    state='UNKNOWN';local={};restarts=0;last_restart=None
    for e in sorted(events,key=lambda e:dt(e['date'])):
        when=dt(e['date'])
        if when>cutoff:break
        message=(e.get('message') or '').upper().strip()
        flag=e.get('flag');scope=e.get('scope');sector=str(e.get('sector'))
        if scope=='Sector':
            if flag in {'YELLOW','DOUBLE YELLOW'}:local[sector]=flag
            elif flag in {'CLEAR','GREEN'}:local.pop(sector,None)
        if flag=='RED' or message.startswith('RED FLAG - RACE SUSPENDED') or message=='SESSION ABORTED':
            state='RED'
        elif message=='VIRTUAL SAFETY CAR DEPLOYED':state='VSC'
        elif message=='SAFETY CAR DEPLOYED':state='SC'
        elif message=='SESSION STARTED':
            if state=='RED':
                # Resumption may be behind the safety car. Do not assume racing green.
                state='RESTART';restarts+=1;last_restart=when
            elif state=='UNKNOWN':state='GREEN'
        elif scope=='Track' and flag=='GREEN' and 'PIT EXIT' not in message:
            if state in {'RED','SC','VSC','RESTART'}:restarts+=1;last_restart=when
            state='GREEN'
        elif message in {'SAFETY CAR IN THIS LAP','VIRTUAL SAFETY CAR ENDING'}:
            # An announcement is not proof that the neutralisation has ended.
            pass
        elif message in {'SAFETY CAR WITHDRAWN','VIRTUAL SAFETY CAR ENDED'}:
            restarts+=1;last_restart=when;state='GREEN'
    return {'state':state,'local_yellow_sectors':len(local),'restart_count':restarts,
            'seconds_since_restart':(cutoff-last_restart).total_seconds() if last_restart else -1.}
