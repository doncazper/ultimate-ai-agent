PYTHON := .venv/bin/python
FRONTEND_DIR := apps/control-center
VERIFY_TIMINGS_JSON ?= /tmp/uaa_verify_all_timings.json
VERIFY_DEV_FAST_JOBS ?= 4

.PHONY: doctor test verify verify-static verify-gate-architecture verify-fast verify-dev-fast verify-local frontend-check frontend-visual-check openapi ruff

doctor:
	$(PYTHON) scripts/verify_dev_environment.py

test:
	PYTHONPATH=src $(PYTHON) -m pytest

verify:
	$(PYTHON) scripts/verify_all.py
	PYTHONPATH=src $(PYTHON) scripts/verify_gate_architecture.py
	$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only

verify-static:
	$(PYTHON) scripts/verify_all.py --skip-ruff --skip-pytest --timings-json $(VERIFY_TIMINGS_JSON)

verify-gate-architecture:
	PYTHONPATH=src $(PYTHON) scripts/verify_gate_architecture.py

verify-fast: ruff test verify-static verify-gate-architecture
	$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only --no-write-latest

verify-dev-fast:
	$(MAKE) -j$(VERIFY_DEV_FAST_JOBS) ruff test verify-static verify-gate-architecture
	$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only --no-write-latest

verify-local: verify-dev-fast

frontend-check:
	cd $(FRONTEND_DIR) && npm run typecheck --if-present
	cd $(FRONTEND_DIR) && npm run lint --if-present
	cd $(FRONTEND_DIR) && npm run test --if-present -- --run
	cd $(FRONTEND_DIR) && npm run build --if-present

frontend-visual-check:
	cd $(FRONTEND_DIR) && npm run visual:check

openapi:
	PYTHONPATH=src $(PYTHON) scripts/export_openapi.py

ruff:
	$(PYTHON) -m ruff check .
