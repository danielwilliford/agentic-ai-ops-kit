from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from app.models import RunManifest


def summarize_runs(runs: list[RunManifest]) -> dict[str, Any]:
    status_counts = Counter(run.status.value for run in runs)
    lane_counts = Counter(run.selected_lane or "unrouted" for run in runs)
    risk_flags = Counter(
        flag
        for run in runs
        if run.packet is not None
        for flag in run.packet.risk_flags
    )
    eval_scores = [run.eval.score for run in runs if run.eval is not None]
    return {
        "total_runs": len(runs),
        "status_counts": dict(sorted(status_counts.items())),
        "lane_counts": dict(sorted(lane_counts.items())),
        "human_gate_count": sum(1 for run in runs if run.requires_human_gate),
        "blocked_runs": sum(1 for run in runs if run.blocked_action is not None),
        "eval_pass_count": sum(1 for run in runs if run.eval is not None and run.eval.passed),
        "avg_eval_score": round(mean(eval_scores), 2) if eval_scores else None,
        "total_estimated_cost_units": round(sum(run.estimated_cost_units for run in runs), 2),
        "risk_flag_counts": dict(sorted(risk_flags.items())),
    }
