from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, HttpUrl
from pathlib import Path
from .url_shortener import URLShortener
app=FastAPI(title='URL Shortener API',version='1.0.0')
service=URLShortener('url_shortener.db')
class CreateURL(BaseModel): url: HttpUrl
@app.get('/',response_class=HTMLResponse)
def home(): return (Path(__file__).parent/'static'/'index.html').read_text(encoding='utf-8')
@app.post('/api/urls',status_code=201)
def create(body:CreateURL):
    try:
        item=service.shorten(str(body.url)); return {**item,'short_url':f'/{item["code"]}'}
    except ValueError as e: raise HTTPException(422,str(e))
@app.get('/api/urls')
def list_urls():
    return service.list_urls()
@app.get('/api/urls/{code}/analytics')
def analytics(code:str):
    item=service.analytics(code)
    if item is None: raise HTTPException(404,'Short code not found')
    return item
@app.get('/{code}')
def redirect(code:str):
    url=service.resolve(code)
    if url is None: raise HTTPException(404,'Short code not found')
    return RedirectResponse(url,status_code=307)
