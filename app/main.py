from pathlib import Path
from io import BytesIO
import zipfile
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from pydantic import BaseModel, HttpUrl
from .url_shortener import URLShortener
from fastapi.staticfiles import StaticFiles
from .models import RunRequest, ApprovalRequest
from .orchestrator import WorkflowOrchestrator, SCENARIOS
from .config import settings

app=FastAPI(title="Agentic Software Engineering System",version="1.0.0",description="Dependency-aware engineering workflow with validation and human approval.")
engine=WorkflowOrchestrator(settings.artifact_dir,settings.max_retries)
DEMO_DIR=Path(__file__).resolve().parents[1]/"examples"/"url-shortener"/"output"
demo_service=URLShortener(str(DEMO_DIR/"url_shortener.db"))
class DemoCreate(BaseModel):
    url: HttpUrl
WEB=Path(__file__).resolve().parents[1]/"web"
app.mount("/static",StaticFiles(directory=str(WEB)),name="static")
@app.get("/",response_class=HTMLResponse)
def home(): return (WEB/"index.html").read_text(encoding="utf-8")
@app.get("/favicon.ico")
def favicon():
    # A tiny SVG favicon avoids noisy browser 404s without requiring a binary asset.
    from fastapi.responses import Response
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#4d68d9"/><path d="M18 16h28v8H26v8h16v8H26v8h20v8H18z" fill="white"/></svg>'
    return Response(svg, media_type="image/svg+xml")
@app.get("/api/health")
def health(): return {"status":"ok","service":"ases","default_mode":"mock"}
@app.get("/api/scenarios")
def scenarios(): return SCENARIOS
@app.post("/api/runs")
def create_run(req:RunRequest):
    run_id=uuid4().hex[:12]
    try: return engine.start(run_id,req.requirement,req.scenario,req.mode,req.repository_context)
    except Exception as exc: raise HTTPException(status_code=500,detail=f"Workflow failed: {type(exc).__name__}: {exc}")
@app.get("/api/runs/{run_id}")
def get_run(run_id:str):
    run=engine.runs.get(run_id)
    if not run: raise HTTPException(status_code=404,detail="Run not found in this process. Runs are in-memory in this prototype.")
    return engine.public_view(run)
@app.post("/api/runs/{run_id}/approve")
def approve(run_id:str,req:ApprovalRequest):
    try: return engine.approve(run_id,req.approved,req.reviewer,req.comment)
    except KeyError: raise HTTPException(status_code=404,detail="Run not found")
    except ValueError as exc: raise HTTPException(status_code=409,detail=str(exc))
@app.get("/api/runs/{run_id}/artifacts/download")
def download_artifacts(run_id: str):
    """Download the complete generated artifact set as one ZIP archive."""
    run = engine.runs.get(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if run.get("status") in {"running", "failed"} or not run.get("artifacts"):
        raise HTTPException(status_code=409, detail="Artifacts are not ready to download")
    base = Path(run.get("artifacts_dir", "")).resolve()
    if not base.is_dir():
        raise HTTPException(status_code=404, detail="Artifact directory not found")
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in run["artifacts"]:
            target = (base / name).resolve()
            if base not in target.parents or not target.is_file():
                continue
            bundle.write(target, arcname=Path(name).as_posix())
    if not archive.getbuffer().nbytes:
        raise HTTPException(status_code=404, detail="No generated artifacts were available to package")
    from fastapi.responses import Response
    return Response(
        content=archive.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="agentic-sdlc-artifacts-{run_id}.zip"'},
    )


@app.get("/api/runs/{run_id}/artifacts/{artifact_path:path}")
def get_artifact(run_id:str,artifact_path:str):
    run=engine.runs.get(run_id)
    if not run: raise HTTPException(status_code=404,detail="Run not found")
    base=Path(run["artifacts_dir"]).resolve(); target=(base/artifact_path).resolve()
    if base not in target.parents or not target.is_file(): raise HTTPException(status_code=404,detail="Artifact not found")
    return FileResponse(target,filename=target.name)


def _require_demo_approval():
    """Keep the runnable assignment locked until a completed run is approved."""
    latest_run = next(reversed(engine.runs.values()), None) if engine.runs else None
    approved = bool(latest_run and latest_run.get("approval", {}).get("status") == "approved")
    if not approved:
        raise HTTPException(
            status_code=403,
            detail="URL Shortener demo is locked. Complete the engineering workflow and approve the result first.",
        )

@app.get("/demo", response_class=HTMLResponse)
def demo_home():
    _require_demo_approval()
    page = """<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ShortLink · Generated URL Shortener</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f4f6fb;color:#1b2940;font:15px/1.5 Inter,system-ui,sans-serif}.top{height:64px;background:#fff;border-bottom:1px solid #e5eaf2;padding:0 max(24px,calc((100vw - 1080px)/2));display:flex;align-items:center;justify-content:space-between}.brand{font-weight:800;color:#435ed0}.wrap{max-width:900px;margin:48px auto;padding:0 20px}.card{background:#fff;border:1px solid #e4e9f1;border-radius:16px;padding:26px;margin-bottom:18px;box-shadow:0 12px 32px #17284a0a}h1{font-size:27px;margin:4px 0 8px}p,.muted{color:#718097}.form{display:grid;grid-template-columns:1fr auto;gap:10px;margin-top:20px}input,button{font:inherit;padding:12px;border-radius:9px}input{border:1px solid #dce2ed;min-width:0}button{border:0;background:#4d68d9;color:white;cursor:pointer;font-weight:700}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:13px 0;border-bottom:1px solid #edf0f5}.row:last-child{border:0}.short{color:#405bd1;font-weight:700}.tiny{font-size:12px;color:#718097;overflow-wrap:anywhere}.actions{display:flex;gap:8px}.secondary{background:#f1f4ff;color:#405bd1;padding:8px 10px}.result{display:none;background:#eef2ff;padding:14px;border-radius:10px;margin-top:14px}.error{color:#b42318}.tag{font-size:11px;background:#eef7f1;color:#17865a;padding:4px 8px;border-radius:20px}@media(max-width:600px){.form{grid-template-columns:1fr}.row{align-items:flex-start;flex-direction:column}}
    </style></head><body><header class="top"><div class="brand">● ShortLink <span style="color:#718097;font-weight:500">generated service</span></div><span class="muted">Agentic SDLC Studio · Live demo</span></header><main class="wrap"><section class="card"><span class="tag">RUNNABLE GENERATED APPLICATION</span><h1>Shorten a URL</h1><p>Create a shareable short link, open it to test redirects, and inspect click analytics. Your original URL stays in the field; success and validation errors appear below.</p><form id="form" class="form"><input id="url" type="url" required placeholder="https://www.example.com/a/very/long/link"><button type="submit">Shorten URL →</button></form><div id="result" class="result"></div></section><section class="card"><div style="display:flex;justify-content:space-between;align-items:center"><div><h2 style="margin:0">Links created in this demo</h2><p class="muted" style="margin:4px 0">Saved in the local SQLite database. Open a short link to increment its click count.</p></div><button class="secondary" onclick="loadLinks()">Refresh</button></div><div id="links" class="muted" style="padding:22px 0;text-align:center">No links yet — shorten your first URL above.</div></section></main><script>
    const $=id=>document.getElementById(id);async function api(url,options={}){const response=await fetch(url,options);const data=await response.json().catch(()=>({detail:'The server returned an invalid response.'}));if(!response.ok)throw new Error(data.detail||`Request failed (${response.status})`);return data}async function loadLinks(){try{const items=await api('/demo/api/urls');$('links').innerHTML=items.length?items.map(x=>`<div class="row"><div><a class="short" target="_blank" rel="noopener" href="/demo/${encodeURIComponent(x.code)}">${location.origin}/demo/${x.code}</a><div class="tiny">${x.original_url}</div></div><div class="actions"><span class="tag">${x.click_count} clicks</span><button class="secondary" type="button" onclick="analytics('${x.code}')">Analytics</button><button class="secondary" type="button" onclick="copyLink('${x.code}')">Copy</button></div></div>`).join(''):'No links yet — shorten your first URL above.'}catch(err){$('links').innerHTML='<span class="error">'+escapeHtml(err.message)+'</span>'}}function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}async function copyLink(code){const value=location.origin+'/demo/'+code;try{await navigator.clipboard.writeText(value);$('result').textContent='Short link copied: '+value;$('result').style.display='block'}catch(e){$('result').textContent='Copy unavailable in this browser. Select the short link to copy it.';$('result').style.display='block'}}async function analytics(code){try{const d=await api('/demo/api/urls/'+encodeURIComponent(code)+'/analytics');alert('Code: '+d.code+'\\nClicks: '+d.click_count+'\\nOriginal URL: '+d.original_url)}catch(err){alert(err.message)}}$('form').addEventListener('submit',async e=>{e.preventDefault();const button=$('form').querySelector('button');const value=$('url').value.trim();$('result').style.display='block';$('result').textContent='Creating your short link…';button.disabled=true;try{const d=await api('/demo/api/urls',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:value})});const short=location.origin+'/demo/'+d.code;$('result').innerHTML=`<strong>${d.created?'Short link created':'Existing short link found'}:</strong> <a class="short" target="_blank" rel="noopener" href="/demo/${encodeURIComponent(d.code)}">${short}</a> <button class="secondary" type="button" onclick="copyLink('${d.code}')">Copy link</button>`;await loadLinks()}catch(err){$('result').innerHTML='<span class="error">'+escapeHtml(err.message)+'</span>'}finally{button.disabled=false}});loadLinks();
    </script></body></html>"""
    return HTMLResponse(page)

@app.post("/demo/api/urls", status_code=201)
def demo_create(body: DemoCreate):
    _require_demo_approval()
    try:
        item=demo_service.shorten(str(body.url))
        return {**item, "short_url": f"/demo/{item['code']}"}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/demo/api/urls")
def demo_list():
    _require_demo_approval()
    return demo_service.list_urls()

@app.get("/demo/api/urls/{code}/analytics")
def demo_analytics(code: str):
    _require_demo_approval()
    item=demo_service.analytics(code)
    if item is None: raise HTTPException(status_code=404, detail="Short code not found")
    return item

@app.get("/demo/{code}")
def demo_redirect(code: str):
    _require_demo_approval()
    url=demo_service.resolve(code)
    if url is None: raise HTTPException(status_code=404, detail="Short code not found")
    return RedirectResponse(url, status_code=307)
