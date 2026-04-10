from datetime import datetime, timedelta
from pathlib import Path

import yaml
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="taskctl API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

TASKCTL_DIR = Path.home() / ".taskctl"


def _load_range(days: int) -> list[dict]:
    if not TASKCTL_DIR.exists():
        return []
    now = datetime.now()
    tasks = []
    for offset in range(days):
        dt = now - timedelta(days=offset)
        date_str = dt.strftime("%d%B%Y").lower()
        path = TASKCTL_DIR / f"tasks-created-{date_str}.yaml"
        if path.exists():
            with path.open("r") as f:
                data = yaml.safe_load(f) or []
            tasks.extend(data)
    return tasks


@app.get("/api/tasks")
def get_tasks(days: int = Query(default=7, ge=1, le=365)) -> list[dict]:
    return _load_range(days)
