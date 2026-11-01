"""Read-only, allowlisted historical replay serving; no ML runtime required."""
import hashlib
import json
import logging
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

router=APIRouter()
TYPES={'index.html':'text/html','demo.js':'text/javascript','data.json':'application/json'}
SECURITY_HEADERS={
    'Cache-Control':'no-cache',
    'X-Content-Type-Options':'nosniff',
    'Referrer-Policy':'no-referrer',
    'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'",
}

def _manifest(root):
    manifest=json.loads((root/'manifest.json').read_text())
    if manifest.get('schema')==2 and isinstance(manifest.get('files'),dict):
        return manifest,manifest['files'],manifest.get('export_mode','aggregate')
    if isinstance(manifest,dict):
        return manifest,manifest,'legacy_full'
    raise ValueError('Unsupported replay manifest')

def serve(asset):
    if asset not in TYPES:raise HTTPException(404,'Unknown replay asset')
    directory=os.environ.get('F1_DEMO_EXPORT')
    if not directory:raise HTTPException(503,'Historical replay is not configured')
    try:
        root=Path(directory);manifest,files,_mode=_manifest(root)
        raw=(root/asset).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=files[asset]:raise ValueError('Replay checksum mismatch')
        return Response(raw,media_type=TYPES[asset],headers=SECURITY_HEADERS)
    except Exception:
        logging.getLogger(__name__).exception('Replay package unavailable')
        raise HTTPException(503,'Replay unavailable or integrity check failed')

@router.get('/model-demo/',include_in_schema=False)
def page():return serve('index.html')

@router.get('/model-demo/export-metadata.json',include_in_schema=False)
def metadata():
    directory=os.environ.get('F1_DEMO_EXPORT')
    if not directory:raise HTTPException(503,'Historical replay is not configured')
    try:
        manifest,_files,mode=_manifest(Path(directory))
        body=json.dumps({'manifest_schema':manifest.get('schema',1),'export_mode':mode}).encode()
        return Response(body,media_type='application/json',headers=SECURITY_HEADERS)
    except Exception:
        logging.getLogger(__name__).exception('Replay metadata unavailable')
        raise HTTPException(503,'Replay unavailable or integrity check failed')

@router.get('/model-demo/{asset}',include_in_schema=False)
def asset(asset:str):return serve(asset)
