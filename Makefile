PYTHON := .venv/bin/python
FRONTEND_DIR := apps/control-center
VERIFY_TIMINGS_JSON ?= /tmp/uaa_verify_all_timings.json
VERIFY_DEV_FAST_JOBS ?= 4
PYTEST_SHARDS ?= 9
PYTEST_SHARD_WORKERS ?= 4
PYTEST_SHARD_TIMINGS_JSON ?= /tmp/uaa_pytest_file_timings.json
PYTEST_SHARD_TIMING_SEED_JSON ?= scripts/verification/pytest_file_timing_seed.json
PYTEST_SHARD_BASETEMP ?= /tmp/uaa_pytest_shards
PYTEST_STRETCH_GOAL_SECONDS ?= 110
PYTEST_TARGET_SECONDS ?= 125
PYTEST_HARD_TIMEOUT_SECONDS ?= 180
PYTEST_PERFORMANCE_REPORT ?= /tmp/uaa_pytest_performance_report.json
CI_SHA ?= $(shell git rev-parse HEAD)
CI_LANE ?= ci-lint
CI_TEMP_ROOT ?= /tmp/uaa-ci-lane
CI_SHARD_INDEX ?= 0
VERIFICATION_EXECUTION_FENCE_ROOT ?= /private/tmp/uaa-verification-execution-fence-v2-$(shell /usr/bin/id -u)
.PHONY: doctor test test-serial test-sharded test-sharded-profile verify verify-static verify-gate-architecture verify-fast verify-affected verify-value-audit verify-dev-fast verify-dev-sharded verify-local verify-beta-local verify-beta-local-visual ci-manifest ci-lane ci-reproduce-shard ci-fallback ci-fallback-status frontend-check frontend-visual-check frontend-turn-router-smoke openapi ruff

doctor:
	$(PYTHON) scripts/verify_dev_environment.py

test:
	$(MAKE) test-sharded

test-serial:
	PYTHONPATH=src $(PYTHON) -m pytest

test-sharded:
	PYTHONPATH=src $(PYTHON) scripts/verification/run_local_verification_lane.py --lane ci-pytest-shards --fence-root $(VERIFICATION_EXECUTION_FENCE_ROOT)

test-sharded-profile:
	PYTHONPATH=src $(PYTHON) scripts/verification/run_local_verification_lane.py --lane ci-pytest-shards --fence-root $(VERIFICATION_EXECUTION_FENCE_ROOT) --profile-output $(PYTEST_SHARD_TIMINGS_JSON)

verify:
	$(MAKE) ruff test-sharded verify-static
	PYTHONPATH=src $(PYTHON) scripts/verify_gate_architecture.py
	$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only

verify-static:
	$(PYTHON) scripts/verify_all.py --skip-ruff --skip-pytest --timings-json $(VERIFY_TIMINGS_JSON)

verify-gate-architecture:
	PYTHONPATH=src $(PYTHON) scripts/verify_gate_architecture.py

verify-fast:
	PYTHONPATH=src $(PYTHON) scripts/verification/changed_path_selector.py --tier fast --execute

verify-affected:
	PYTHONPATH=src $(PYTHON) scripts/verification/changed_path_selector.py --tier affected --execute

verify-value-audit:
	PYTHONPATH=src $(PYTHON) scripts/verification/verifier_value_audit.py

verify-dev-fast:
	$(MAKE) -j$(VERIFY_DEV_FAST_JOBS) ruff test verify-static verify-gate-architecture
	$(PYTHON) scripts/run_foundation_gate.py --command-mode report-only --no-write-latest

verify-dev-sharded:
	PYTHONPATH=src $(PYTHON) scripts/verification/run_dev_fast_gate.py \
		--jobs $(VERIFY_DEV_FAST_JOBS) \
		--pytest-shards $(PYTEST_SHARDS) \
		--pytest-workers $(PYTEST_SHARD_WORKERS) \
		--static-timings-json $(VERIFY_TIMINGS_JSON)

verify-local: verify-dev-sharded

ci-manifest:
	$(PYTHON) scripts/verification/ci_command_manifest.py

ci-lane:
	$(PYTHON) scripts/verification/run_ci_lane.py --lane $(CI_LANE) --sha $(CI_SHA) --temp-root $(CI_TEMP_ROOT)

ci-reproduce-shard:
	$(PYTHON) scripts/verification/run_ci_lane.py --lane ci-pytest-shard-$(CI_SHARD_INDEX)-reproduce --sha $(CI_SHA) --temp-root $(CI_TEMP_ROOT)

ci-fallback:
	$(PYTHON) scripts/ci/verify_with_fallback.py --repo . --sha $(CI_SHA) --mode github-first

ci-fallback-status:
	$(PYTHON) scripts/ci/verify_with_fallback.py --repo . --sha $(CI_SHA) --mode status

verify-beta-local:
	$(PYTHON) scripts/verify_beta_local.py

verify-beta-local-visual:
	$(PYTHON) scripts/verify_beta_local.py --include-live-visual

frontend-check:
	PYTHONPATH=src $(PYTHON) scripts/verification/run_local_verification_lane.py --lane ci-control-center-frontend --fence-root $(VERIFICATION_EXECUTION_FENCE_ROOT)

frontend-visual-check:
	$(PYTHON) scripts/verification/run_frontend_playwright.py --suite visual

frontend-turn-router-smoke:
	$(PYTHON) scripts/verification/run_frontend_playwright.py --suite smoke

openapi:
	PYTHONPATH=src $(PYTHON) scripts/export_openapi.py

ruff:
	$(PYTHON) -m ruff check .

portable-evidence-keychain-helper:
	$(PYTHON) scripts/dev/install_portable_evidence_keychain_helper.py

governed-browser-keychain-helper:
	$(PYTHON) scripts/dev/install_governed_browser_keychain_helper.py

.PHONY: portable-evidence-keychain-helper governed-browser-keychain-helper
