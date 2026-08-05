"""State/resume pattern: embeds `_pipeline_state` directly inside the
project's own data JSON, per-stage status+timestamp+artifacts -- so artifact
and state are always read/written together, never a separate checkpoint file
that can drift out of sync with what's actually on disk. Pattern observed for
real in youtube-shorts-pipeline (MIT, data/references/e2e-pipeline/NOTES.md
#1) -- reimplemented independently here, not copied verbatim, for this
project's own scene-based schema."""
from __future__ import annotations

import json
import time
from pathlib import Path


class PipelineState:
    def __init__(self, project_json_path: Path):
        self.path = project_json_path
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self.data = {}
        self.data.setdefault("_pipeline_state", {})

    def is_done(self, stage: str) -> bool:
        return self.data["_pipeline_state"].get(stage, {}).get("status") == "done"

    def mark_done(self, stage: str, artifacts: list[str] | None = None) -> None:
        self.data["_pipeline_state"][stage] = {
            "status": "done",
            "timestamp": time.time(),
            "artifacts": artifacts or [],
        }
        self.save()

    def mark_failed(self, stage: str, error: str) -> None:
        self.data["_pipeline_state"][stage] = {
            "status": "failed",
            "timestamp": time.time(),
            "error": error,
        }
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
