.PHONY: verify reports

verify:
	pytest -q

reports:
	python -m app.demo_reports --out examples/enterprise_controls
