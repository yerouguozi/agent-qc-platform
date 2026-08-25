from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import agents, datasets, metrics, proxy, review, runs, traces
from app.core.config import settings
from app.core.db import Base, engine
from app.schemas import HealthOut


def _ensure_columns() -> None:
    """轻量迁移:老库补新列,新库由 create_all 直接建好。"""
    from sqlalchemy import inspect, text

    tables = set(inspect(engine).get_table_names())
    for table, column, ddl in (
        ("agents", "chat_url", "VARCHAR(500)"),
        ("agents", "auth_token", "TEXT"),
        ("agents", "dataset_id", "VARCHAR(100)"),
        ("agents", "driver_type", "VARCHAR(20)"),
        ("eval_runs", "agent_id", "VARCHAR(32)"),
    ):
        if table in tables:
            cols = {c["name"] for c in inspect(engine).get_columns(table)}
            if column not in cols:
                with engine.begin() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
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