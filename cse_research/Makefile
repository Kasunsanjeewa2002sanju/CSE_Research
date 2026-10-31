.PHONY: help install test smoke stage clean

PYTHON ?= .venv/Scripts/python.exe
UV ?= uv

help:
	@echo "CSE Research Project Commands:"
	@echo "  make install      - Install dependencies into virtual environment"
	@echo "  make test         - Run test suite"
	@echo "  make smoke        - Run environment smoke test"
	@echo "  make stage S=0    - Execute pipeline stage N (e.g. make stage S=0)"
	@echo "  make clean        - Remove caches and build artifacts"

install:
	$(UV) pip install --link-mode=copy -r requirements.txt

test:
	$(PYTHON) -m pytest tests/ -v

smoke:
	$(PYTHON) -m pytest tests/test_smoke.py -v

stage:
	$(PYTHON) -m cse.run --stage $(S)

clean:
	powershell -Command "Get-ChildItem -Path . -Include __pycache__, .pytest_cache -Recurse | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue"
