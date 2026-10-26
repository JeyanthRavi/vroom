"""Synthetic storage-scale smoke check; never writes fixtures to the real library.

Run from the project with the same PYTHONPATH as the server. This is NOT a
concurrent-user load test or proof of real provider coverage.
"""
import json
import tempfile
import time
from pathlib import Path
from f1_intelligence_lab.library import Library
from telemetry_pit_crew.sample_data import demo_laps


def main():
    with tempfile.TemporaryDirectory(prefix='race-library-bench-') as root:
        library=Library(Path(root))
        base=next(iter(demo_laps().values()))
        start=time.perf_counter()
        for index in range(100):
            key=f'benchmark-{index}'
            laps=[base.model_copy(update={'id':f'{key}-{driver}','driver':f'D{driver:02d}'}) for driver in range(20)]
            library.store({'id':key,'source_type':'synthetic_benchmark'},laps)
        write_ms=(time.perf_counter()-start)*1000
        start=time.perf_counter();sessions=library.sessions();catalog_ms=(time.perf_counter()-start)*1000
        start=time.perf_counter();summaries=library.lap_summaries('benchmark-50');summary_ms=(time.perf_counter()-start)*1000
        start=time.perf_counter();lap=library.lap('benchmark-50-1');lap_ms=(time.perf_counter()-start)*1000
        assert len(sessions)==100 and len(summaries)==20 and len(lap.samples)>0
        assert all('samples' not in row for row in summaries)
        print(json.dumps({'scope':'synthetic SQLite storage smoke check; not concurrent-user load',
            'sessions':len(sessions),'telemetry_laps':2000,'samples_per_lap':len(lap.samples),
            'write_ms':round(write_ms,1),'metadata_catalog_ms':round(catalog_ms,1),
            'one_session_summaries_ms':round(summary_ms,1),'one_lap_load_ms':round(lap_ms,1)},indent=2))


if __name__=='__main__':main()
