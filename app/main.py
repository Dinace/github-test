from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers.clients import router as clients_router
from app.routers.maintenance import router as maintenance_router
from app.routers.maintenance import sentry_webhook_router
from app.routers.planning import client_router as planning_client_router
from app.routers.planning import staff_router as planning_staff_router
from app.routers.posts import router as posts_router
from app.routers.prospection import router as prospection_router
from app.routers.sites import router as sites_router
from platform_core.config import settings
from platform_core.scheduler import create_scheduler

# Instrumentation Sentry réelle de l'app elle-même (pas seulement des sites clients
# générés) — n'envoie rien si SENTRY_DSN est vide (dev/test).
if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.0)

BASE_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Démarre les tâches planifiées (voir platform_core/scheduler.py) à côté de l'app —
    # jamais déclenché par la suite de tests, qui instancie `TestClient(app)` sans bloc
    # `with` (les événements de lifespan ASGI ne se déclenchent alors pas).
    scheduler = create_scheduler()
    scheduler.start()
    app.state.scheduler = scheduler
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="Plateforme de digitalisation PME/indépendants", lifespan=_lifespan)
app.include_router(clients_router)
app.include_router(sites_router)
app.include_router(posts_router)
app.include_router(maintenance_router)
app.include_router(sentry_webhook_router)
app.include_router(prospection_router)
app.include_router(planning_staff_router)
app.include_router(planning_client_router)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def dashboard_home(request: Request):
    return templates.TemplateResponse(request, "index.html", {})
