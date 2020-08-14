.PHONY: lint format_style format_imports test test_std test_multiproc

all: lint format_style format_imports test

lint:
	poetry run flake8 --config .flake8 --statistics

format_style:
	poetry run black .

format_imports:
	poetry run isort --profile black .

test: test_std test_multiproc

test_std:
	poetry run pytest --cov=./ --cov-report=xml

test_multiproc:
	mkdir -p /tmp/test_multiproc; \
	export prometheus_multiproc_dir=/tmp/test_multiproc; \
	poetry run pytest -k test_multiprocess_reg --cov-append --cov=./ --cov-report=xml; \
	rm -rf /tmp/test_multiproc; \
	unset prometheus_multiproc_dir;
