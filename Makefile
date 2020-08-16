.PHONY: all
all: lint format_style format_imports test docs requirements

.PHONY: lint
lint:
	poetry run flake8 --config .flake8 --statistics

.PHONY: format_style
format_style:
	poetry run black .

.PHONY: format_imports
format_imports:
	poetry run isort --profile black .

.PHONY: test
test: test_std test_multiproc

.PHONY: test_std
test_std:
	poetry run pytest --cov=./ --cov-report=xml

.PHONY: test_multiproc
test_multiproc:
	mkdir -p /tmp/test_multiproc; \
	export prometheus_multiproc_dir=/tmp/test_multiproc; \
	poetry run pytest -k test_multiprocess_reg --cov-append --cov=./ --cov-report=xml; \
	rm -rf /tmp/test_multiproc; \
	unset prometheus_multiproc_dir;

.PHONY: docs
docs:
	rm -rf html/*; pdoc --html prometheus_fastapi_instrumentator

.PHONY: requirements
requirements:
	poetry run pip freeze > requirements.txt
