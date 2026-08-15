from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, datasets, metrics, proxy, review, runs, traces
from app.core.config import settings
from app.core.db import Base, engine
from app.schemas import HealthOut


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    Base.metadata.create_all(bind=engine)
    app.include_router(agents.router)
    app.include_router(proxy.router)
    app.include_router(traces.router)
    app.include_router(datasets.router)
    app.include_router(runs.router)
    app.include_router(metrics.router)
    app.include_router(review.router)

    @app.get("/health", response_model=HealthOut)
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()