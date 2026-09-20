from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers.clients import router as clients_router
from app.routers.sites import router as sites_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Plateforme de digitalisation PME/indépendants")
app.include_router(clients_router)
app.include_router(sites_router)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def dashboard_home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})
