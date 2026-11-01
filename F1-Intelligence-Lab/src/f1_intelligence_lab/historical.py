"""FastF1 provider adapter. Invoked in a timeout-bounded subprocess."""
import csv
import io
import math
from datetime import datetime, timezone

from .library import Library
from .race_analysis import FIELDS, analyze


def track_flag(status):
    value = str(status)
    if '5' in value: return 'RED'
    if '4' in value: return 'SC'
    if '6' in value or '7' in value: return 'VSC'
    if value == '1': return 'GREEN'
    return 'UNKNOWN'  # Yellow/missing/mixed non-green status must not become clean.


def race_csv(frame):
    """Preserve valid timings; conservatively exclude provider-marked unreliable laps."""
    import pandas as pd
    out = io.StringIO()
    writer = csv.writer(out, lineterminator='\n')
    writer.writerow(FIELDS)
    skipped = 0
    for _, r in frame.iterrows():
        if any(pd.isna(r.get(k)) for k in ['Driver','LapNumber','LapTime','Stint']):
            skipped += 1
            continue
        seconds = r['LapTime'].total_seconds()
        if not math.isfinite(seconds) or not 1 <= seconds <= 3600:
            skipped += 1
            continue
        compound = str(r.get('Compound', 'UNKNOWN'))
        if compound not in {'SOFT','MEDIUM','HARD','INTERMEDIATE','WET'}: compound = 'UNKNOWN'
        flag = track_flag(r.get('TrackStatus', ''))
        inaccurate = pd.isna(r.get('IsAccurate')) or not bool(r.get('IsAccurate'))
        deleted = not pd.isna(r.get('Deleted')) and bool(r.get('Deleted'))
        generated = not pd.isna(r.get('FastF1Generated')) and bool(r.get('FastF1Generated'))
        if flag == 'GREEN' and (inaccurate or deleted or generated or not pd.isna(r.get('PitOutTime'))):
            flag = 'UNKNOWN'
        writer.writerow([str(r['Driver']),int(r['LapNumber']),seconds,compound,int(r['Stint']),
                         int(not pd.isna(r.get('PitInTime'))),flag])
    return out.getvalue(), skipped


def import_session(library, year, event, code, progress=lambda message: None):
    import fastf1
    import pandas as pd
    from telemetry_pit_crew.ingestion import from_fastf1_lap
    cache = library.root / 'provider-cache'
    cache.mkdir(exist_ok=True)
    fastf1.Cache.enable_cache(str(cache))
    progress('Downloading timing and telemetry; first load may take several minutes.')
    session = fastf1.get_session(year, event, code)
    session.load(laps=True, telemetry=True, weather=False, messages=False)
    event_name = str(session.event['EventName'])
    round_number = int(session.event['RoundNumber'])
    session_id = f'fastf1-{year}-{round_number}-{code.lower()}'
    if session.laps.empty:
        raise ValueError('Provider returned no lap timing for this session.')
    race = None
    if code in {'R','S'}:
        text, skipped = race_csv(session.laps)
        race = analyze(text, f'{year} {event_name} · {session.name}', 'fastf1_historical')
        race['warnings'].append(f'{skipped} records missing valid timing/driver/stint were omitted. UNKNOWN also excludes provider-inaccurate, generated, deleted and pit-out laps.')
        race['methodology']['clean_laps'] += ' Provider quality flags and explicit pit-out timestamps also exclude laps (mapped to UNKNOWN).'
        race['session_id'] = session_id
    drivers = sorted(str(v) for v in session.laps['Driver'].dropna().unique())
    laps, unavailable = [], []
    for index, driver in enumerate(drivers):
        progress(f'Preparing telemetry {index+1}/{len(drivers)}: {driver}')
        candidates = session.laps.pick_drivers(driver)
        candidates = candidates[candidates['LapTime'].notna()]
        if 'Deleted' in candidates:
            candidates = candidates[~candidates['Deleted'].fillna(False).astype(bool)]
        if 'IsAccurate' in candidates:
            candidates = candidates[candidates['IsAccurate'].fillna(False).astype(bool)]
        converted = None
        for _, candidate in candidates.sort_values('LapTime').head(3).iterlaps():
            try:
                if pd.isna(candidate.get('TyreLife')): candidate['TyreLife'] = 0
                converted = from_fastf1_lap(candidate, event_name, session_id)
                if len(converted.samples) < 3: raise ValueError('Insufficient samples')
                if any(not math.isfinite(float(v)) for s in converted.samples for v in s.model_dump().values()):
                    raise ValueError('Nonfinite telemetry')
                break
            except (ValueError, TypeError, KeyError, IndexError):
                converted = None
        if converted: laps.append(converted)
        else: unavailable.append(driver)
    metadata = {'id': session_id, 'name': f'{year} {event_name} — {code}', 'year': year,
                    'event': event_name, 'session_code': code, 'source_type': 'fastf1_historical',
                    'source_url': 'https://docs.fastf1.dev/', 'source_urls': ['https://docs.fastf1.dev/'],
                    'retrieved_at': datetime.now(timezone.utc).isoformat(),
                    'provider_version': fastf1.__version__, 'drivers_total': len(drivers),
                    'telemetry_drivers': len(laps), 'unavailable_drivers': unavailable,
                    'race_records': race['records'] if race else 0,
                    'notes': 'Historical FastF1 session. Race Lab uses full available lap timing. Other tools use one fastest usable accurate, non-deleted telemetry lap per available driver (up to 3 candidates tried). Not live; not a full-race telemetry replay.'}
    progress('Validating and committing the session atomically.')
    library.store(metadata, laps, race)
    return session_id


if __name__ == '__main__':
    import sys
    lib = Library(sys.argv[1])
    job = lib.job(sys.argv[2])
    args = job['request']
    try:
        if args.get('provider') == 'openf1':
            from .openf1_provider import import_openf1
            loader = import_openf1
        else:
            loader = import_session
        result = loader(lib, args['year'], args['event'], args['session_code'],
                                lambda message: lib.update_job(job['id'], 'running', message))
        lib.update_job(job['id'], 'complete', 'Session saved. Available across the analysis workstations.', result)
    except Exception as exc:
        lib.update_job(job['id'], 'failed', f'{type(exc).__name__}: {str(exc)[:500]}. Retry from the library; existing sessions are unchanged.')
        raise
