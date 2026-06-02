import json
from pathlib import Path

from jsonschema import Draft7Validator

from app.demo_reports import build_enterprise_controls_report

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _validator(schema_name: str) -> Draft7Validator:
    return Draft7Validator(_load_schema(schema_name))


def test_control_report_schemas_are_valid_draft7():
    for name in ("metrics_summary.json", "red_team_review.json", "enterprise_controls_report.json"):
        Draft7Validator.check_schema(_load_schema(name))


def test_generated_control_report_validates_against_schemas():
    report = build_enterprise_controls_report()

    _validator("metrics_summary.json").validate(report["metrics"])
    _validator("red_team_review.json").validate(report["red_team_review"])
    _validator("enterprise_controls_report.json").validate(report)


def test_static_example_control_artifacts_validate_against_schemas():
    examples = ROOT / "examples" / "enterprise_controls"

    _validator("metrics_summary.json").validate(json.loads((examples / "metrics_summary.json").read_text(encoding="utf-8")))
    _validator("red_team_review.json").validate(json.loads((examples / "red_team_review.json").read_text(encoding="utf-8")))
    _validator("enterprise_controls_report.json").validate(json.loads((examples / "enterprise_controls_report.json").read_text(encoding="utf-8")))
