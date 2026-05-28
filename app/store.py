from __future__ import annotations

import json
from pathlib import Path

from app.models import RunManifest

RUN_DIR = Path(__file__).resolve().parent.parent / "runs"
RUN_DIR.mkdir(exist_ok=True)


def save_run(run: RunManifest) -> None:
    (RUN_DIR / f"{run.run_id}.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")


def load_run(run_id: str) -> RunManifest:
    path = RUN_DIR / f"{run_id}.json"
    if not path.exists():
        raise KeyError(run_id)
    return RunManifest.model_validate(json.loads(path.read_text(encoding="utf-8")))
