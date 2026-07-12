PYTHON := .venv/bin/python
FRONTEND_DIR := apps/control-center
VERIFY_TIMINGS_JSON ?= /tmp/uaa_verify_all_timings.json
VERIFY_DEV_FAST_JOBS ?= 4
PYTEST_SHARDS ?= 8
PYTEST_SHARD_WORKERS ?= 8
PYTEST_SHARD_TIMINGS_JSON ?= /tmp/uaa_pytest_file_timings.json
PYTEST_SHARD_TIMING_SEED_JSON ?= scripts/verification/pytest_file_timing_seed.json
PYTEST_SHARD_BASETEMP ?= /tmp/uaa_pytest_shards
PYTEST_STRETCH_GOAL_SECONDS ?= 110
PYTEST_TARGET_SECONDS ?= 125
PYTEST_HARD_TIMEOUT_SECONDS ?= 180
PYTEST_PERFORMANCE_REPORT ?= /tmp/uaa_pytest_performance_report.json

.PHONY: doctor test test-serial test-sharded test-sharded-profile verify verify-static verify-gate-architecture verify-fast verify-dev-fast verify-dev-sharded verify-local verify-beta-local verify-beta-local-visual frontend-check frontend-visual-check frontend-turn-router-smoke openapi ruff

doctor:
	$(PYTHON) scripts/verify_dev_environment.py

test:
	$(MAKE) test-sharded

test-serial:
	PYTHONPATH=src $(PYTHON) -m pytest

test-sharded:
	PYTHONPATH=src $(PYTHON) scripts/verification/run_pytest_shards.py --shards $(PYTEST_SHARDS) --max-workers $(PYTEST_SHARD_WORKERS) --timings-json $(PYTEST_SHARD_TIMING_SEED_JSON) --timings-json $(PYTEST_SHARD_TIMINGS_JSON) --basetemp $(PYTEST_SHARD_BASETEMP) --stretch-goal-seconds $(PYTEST_STRETCH_GOAL_SECONDS) --target-seconds $(PYTEST_TARGET_SECONDS) --hard-timeout-seconds $(PYTEST_HARD_TIMEOUT_SECONDS) --performance-report $(PYTEST_PERFORMANCE_REPORT)

test-sharded-profile:
	PYTHONPATH=src $(PYTHON) scripts/verification/run_pytest_shards.py --shards $(PYTEST_SHARDS) --max-workers $(PYTEST_SHARD_WORKERS) --timings-json $(PYTEST_SHARD_TIMING_SEED_JSON) --timings-json $(PYTEST_SHARD_TIMINGS_JSON) --write-timings-json $(PYTEST_SHARD_TIMINGS_JSON) --basetemp $(PYTEST_SHARD_BASETEMP) --stretch-goal-seconds $(PYTEST_STRETCH_GOAL_SECONDS) --target-seconds $(PYTEST_TARGET_SECONDS) --hard-timeout-seconds $(PYTEST_HARD_TIMEOUT_SECONDS) --performance-report $(PYTEST_PERFORMANCE_REPORT)

verify:
	$(MAKE) ruff test-sharded verify-static
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

verify-dev-sharded:
	PYTHONPATH=src $(PYTHON) scripts/verification/run_dev_fast_gate.py \
		--jobs $(VERIFY_DEV_FAST_JOBS) \
		--pytest-shards $(PYTEST_SHARDS) \
		--pytest-workers $(PYTEST_SHARD_WORKERS) \
		--pytest-timing-seed-json $(PYTEST_SHARD_TIMING_SEED_JSON) \
		--pytest-timings-json $(PYTEST_SHARD_TIMINGS_JSON) \
		--pytest-basetemp $(PYTEST_SHARD_BASETEMP) \
		--static-timings-json $(VERIFY_TIMINGS_JSON)

verify-local: verify-dev-sharded

verify-beta-local:
	$(PYTHON) scripts/verify_beta_local.py

verify-beta-local-visual:
	$(PYTHON) scripts/verify_beta_local.py --include-live-visual

frontend-check:
	cd $(FRONTEND_DIR) && npm run typecheck --if-present
	cd $(FRONTEND_DIR) && npm run lint --if-present
	cd $(FRONTEND_DIR) && npm run test --if-present -- --run
	cd $(FRONTEND_DIR) && npm run build --if-present

frontend-visual-check:
	cd $(FRONTEND_DIR) && npm run visual:check

frontend-turn-router-smoke:
	cd $(FRONTEND_DIR) && npm run smoke:turn-router

openapi:
	PYTHONPATH=src $(PYTHON) scripts/export_openapi.py

ruff:
	$(PYTHON) -m ruff check .
