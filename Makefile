PYTHON := .venv/bin/python
FRONTEND_DIR := apps/control-center

.PHONY: doctor test verify frontend-check openapi ruff

doctor:
	$(PYTHON) scripts/verify_dev_environment.py

test:
	PYTHONPATH=src $(PYTHON) -m pytest

verify:
	$(PYTHON) scripts/verify_current_baseline.py
	$(PYTHON) scripts/verify_documentation_integrity.py
	$(PYTHON) scripts/verify_skill_package_security_rule.py
	$(PYTHON) scripts/verify_control_center_frontend.py
	$(PYTHON) scripts/verify_all.py
	$(PYTHON) scripts/run_foundation_gate.py
	$(PYTHON) scripts/verify_openapi_contract.py
	$(PYTHON) -m ruff check .

frontend-check:
	cd $(FRONTEND_DIR) && npm run typecheck --if-present
	cd $(FRONTEND_DIR) && npm run lint --if-present
	cd $(FRONTEND_DIR) && npm run test --if-present -- --run
	cd $(FRONTEND_DIR) && npm run build --if-present

openapi:
	PYTHONPATH=src $(PYTHON) scripts/export_openapi.py

ruff:
	$(PYTHON) -m ruff check .
