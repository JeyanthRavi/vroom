PYTHON ?= python3
LAB := F1-Intelligence-Lab
PYTHONPATH := $(LAB)/src:F1-StewardLens/src:F1-Telemetry-Pit-Crew/src
TESTS := $(LAB)/tests F1-StewardLens/tests F1-Telemetry-Pit-Crew/tests

.PHONY: setup test test-fast test-torch lint type demo docs

setup:
	bash $(LAB)/scripts/setup.sh
	$(LAB)/.venv/bin/python -m pip install -e '.[dev]'

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q $(TESTS) --import-mode=importlib -rs

test-fast:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q $(LAB)/tests F1-StewardLens/tests F1-Telemetry-Pit-Crew/tests --import-mode=importlib -m 'not slow' --ignore=$(LAB)/tests/test_cross_season.py --ignore=$(LAB)/tests/test_dl_train.py --ignore=$(LAB)/tests/test_restart_evaluate.py --ignore=$(LAB)/tests/test_robust_train.py

test-torch:
	$(PYTHON) -c 'import torch; print("torch", torch.__version__)'
	$(MAKE) test PYTHON=$(PYTHON)

lint:
	$(PYTHON) -m ruff check F1-Intelligence-Lab/src F1-Intelligence-Lab/tests F1-StewardLens/src F1-StewardLens/tests F1-Telemetry-Pit-Crew/src F1-Telemetry-Pit-Crew/tests

type:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m mypy F1-Intelligence-Lab/src F1-StewardLens/src F1-Telemetry-Pit-Crew/src

demo:
	F1_DEMO_EXPORT="$(CURDIR)/$(LAB)/demo-export-aggregate" PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q $(LAB)/tests/test_demo_api.py $(LAB)/tests/test_export_demo.py --import-mode=importlib
	F1_DEMO_EXPORT="$(CURDIR)/$(LAB)/demo-export-aggregate" PYTHONPATH=$(PYTHONPATH) $(PYTHON) -c 'from fastapi.testclient import TestClient; from f1_intelligence_lab.demo_app import app; c=TestClient(app); assert c.get("/health").status_code==200; assert c.get("/model-demo/export-metadata.json").json()["export_mode"]=="aggregate"'

docs:
	$(PYTHON) scripts/check_internal_links.py

