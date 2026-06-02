from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.metrics import summarize_runs
from app.red_team import build_red_team_report, red_team_runs


def build_enterprise_controls_report() -> dict[str, Any]:
    red_team = build_red_team_report()
    metrics = summarize_runs(red_team_runs(red_team))
    return {
        "artifact_type": "enterprise_controls_report",
        "generated_at": red_team["reviewed_at"],
        "summary": {
            "red_team_all_passed": red_team["all_passed"],
            "red_team_case_count": red_team["case_count"],
            "blocked_runs": metrics["blocked_runs"],
            "human_gate_count": metrics["human_gate_count"],
            "total_estimated_cost_units": metrics["total_estimated_cost_units"],
        },
        "metrics": metrics,
        "red_team_review": red_team,
    }


def write_report(out_dir: Path) -> dict[str, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    report = build_enterprise_controls_report()
    metrics_path = out_dir / "metrics_summary.json"
    red_team_path = out_dir / "red_team_review.json"
    report_path = out_dir / "enterprise_controls_report.json"
    metrics_path.write_text(json.dumps(report["metrics"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    red_team_path.write_text(json.dumps(report["red_team_review"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "metrics": metrics_path,
        "red_team": red_team_path,
        "report": report_path,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic public Ops Kit control reports")
    parser.add_argument("--out", type=Path, default=Path("examples") / "enterprise_controls")
    args = parser.parse_args(argv)
    paths = write_report(args.out)
    for name, path in paths.items():
        print(f"{name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
