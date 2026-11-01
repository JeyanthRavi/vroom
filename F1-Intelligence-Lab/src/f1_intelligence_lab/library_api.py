"""Local library routes with a single bounded import worker and durable job state."""
import json
import subprocess
import sys
import threading
import uuid
from collections import ChainMap
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from telemetry_pit_crew.api import service

from .library import LapMap, Library, SessionMap
from .security import require_admin

library = Library()
service.sessions = ChainMap(service.sessions, SessionMap(library))
service.laps = ChainMap(service.laps, LapMap(library))
service.external_summaries = library.lap_summaries
router = APIRouter()
lock = threading.Lock()


class ImportRequest(BaseModel):
    provider: Literal['openf1','fastf1'] = 'openf1'
    year: int = Field(ge=2018, le=2026)
    event: str = Field(min_length=2, max_length=80, pattern=r'^[A-Za-z0-9 .\-]+$')
    session_code: str = Field(pattern=r'^(R|Q|S|SQ|FP1|FP2|FP3)$')


def run_worker(job_id):
    log_path = library.root / f'job-{job_id}.log'
    try:
        with log_path.open('w') as log:
            result = subprocess.run([sys.executable, '-m', 'f1_intelligence_lab.historical',
                                     str(library.root), job_id], stdout=log, stderr=log, timeout=900)
        if library.job(job_id)['state'] not in {'complete','failed'}:
            library.update_job(job_id,'failed',f'Importer exited ({result.returncode}). Inspect local job log and retry.')
    except subprocess.TimeoutExpired:
        library.update_job(job_id,'failed','Download exceeded 15 minutes and was stopped. Cached provider data is retained; retry later.')
    except Exception:
        library.update_job(job_id,'failed','Could not start importer. Check local installation and retry.')


@router.get('/library/', response_class=HTMLResponse, include_in_schema=False)
def library_page():
    return (Path(__file__).parent/'static'/'library.html').read_text()


@router.get('/api/library/sessions', tags=['library'])
def sessions():
    return library.sessions()


@router.get('/api/library/races/{session_id}', tags=['library'])
def race(session_id: str):
    try: return library.race(session_id)
    except KeyError: raise HTTPException(404,'No saved race timing for this session. Choose an imported race or sprint.') from None


@router.get('/api/library/jobs', tags=['library'])
def jobs():
    with library.connect() as db:
        ids = [r[0] for r in db.execute('SELECT id FROM jobs ORDER BY created_at DESC, rowid DESC LIMIT 30')]
    return [library.job(key) for key in ids]


@router.post('/api/library/import', status_code=202, tags=['library'])
def start_import(payload: ImportRequest, _admin: None = Depends(require_admin)):
    request = payload.model_dump()
    request['event'] = request['event'].strip()
    if len(request['event']) < 2:
        raise HTTPException(422,'Enter an event name, such as Monza or Silverstone.')
    with lock, library.connect() as db:
        db.execute("UPDATE jobs SET state='failed',message='Import interrupted or expired. Retry this session.' WHERE state IN ('queued','running') AND created_at < datetime('now','-16 minutes')")
        active = db.execute("SELECT id,request FROM jobs WHERE state IN ('queued','running')").fetchone()
        if active:
            if json.loads(active['request']) == request: return library.job(active['id'])
            raise HTTPException(409,'Another import is running. Wait for it to finish before requesting another session.')
        key = uuid.uuid4().hex
        db.execute("INSERT INTO jobs(id,state,message,request) VALUES(?,?,?,?)",
                   (key,'queued','Waiting for provider download.',json.dumps(request)))
    threading.Thread(target=run_worker,args=(key,),daemon=True).start()
    return library.job(key)
