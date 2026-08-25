"""评测后台执行:接口秒回,线程执行,避免长任务阻塞请求。"""
import threading

from app.core.db import SessionLocal
from app.eval.driver import build_driver
from app.eval.runner import execute_run
from app.models import EvalRun

_workers: dict[str, threading.Thread] = {}


def start_run(run_id: str) -> bool:
    worker = _workers.get(run_id)
    if worker is not None and worker.is_alive():
        return False
    thread = threading.Thread(target=_work, args=(run_id,), daemon=True, name=f"run-{run_id[:8]}")
    _workers[run_id] = thread
    thread.start()
    return True


def _work(run_id: str) -> None:
    db = SessionLocal()
    try:
        run = db.get(EvalRun, run_id)
        if run is None:
            return
        driver = build_driver(db, run=run)
        execute_run(db, run, driver)
    except Exception:
        db.rollback()
        run = db.get(EvalRun, run_id)
        if run is not None:
            run.status = "failed"
            db.commit()
    finally:
        db.close()