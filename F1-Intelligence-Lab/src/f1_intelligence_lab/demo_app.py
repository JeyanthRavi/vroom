"""Minimal public-demo entry point: no import jobs, uploads, weights or raw caches."""
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from .demo_api import router,serve
app=FastAPI(title='Vroom historical ML replay',docs_url=None,redoc_url=None,openapi_url=None)
app.include_router(router)
@app.get('/')
def home():return RedirectResponse('/model-demo/')
@app.get('/health')
def health():
    for name in ['index.html','demo.js','data.json']:serve(name)
    return {'status':'ok','mode':'historical_replay'}
