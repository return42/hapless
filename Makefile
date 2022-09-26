.PHONY: build
build:
	@rm -rf dist/
	@rm -rf build/
	@poetry build

.PHONY: tests
tests:
	@poetry run pytest -sv tests


.PHONY: coverage
coverage:
	@poetry run pytest --cov=hapless tests


.PHONY: coverage-report
coverage-report:
	@poetry run pytest --cov=hapless --cov-report=html tests

.PHONY: pyenv, bash
pyenv:
	@python -m venv ./local/pyenv
	@. ./local/pyenv/bin/activate \
	  && pip install poetry \
	  && poetry install

bash:
	@. ./local/pyenv/bin/activate \
	  && bash
