#!/usr/bin/env bash

project_name="prometheus_fastapi_instrumentator"

# ==============================================================================
# Misc

function _docs {
    echo "Create docs"

    tmp_dir=/tmp/docs
    rm -rf /tmp/docs
    mkdir -p /tmp/docs
    rm -rf docs/*
    mkdir -p docs
    poetry run pdoc --output-dir /tmp/docs --html ${project_name}
    mv /tmp/docs/${project_name}/* docs/
    rm -rf /tmp/docs
}

function _lint {
    echo "Lint project"

    poetry run flake8 --config .flake8 --statistics
    poetry run mypy ${project_name} --allow-redefinition
}

function _requirements {
    echo "Create requirements file"

    rm -rf "requirements.txt"
    poetry export \
        --format "requirements.txt" \
        --output "requirements.txt" \
        --without-hashes
}

# ==============================================================================
# Format

function _format_style {
    echo "Format style"

    poetry run black .    
}

function _format_imports {
    echo "Format imports"

    poetry run isort --profile black .
}

function _format {
    _format_style
    _format_imports
}

# ==============================================================================
# Test

function _test_not_slow {
    echo "Run non-slow tests with Pytest"

    poetry run pytest -m "not slow" --cov=./ --cov-report=xml
}

function _test_slow {
    echo "Run slow tests with Pytest"
    
    poetry run pytest -m "slow" --cov-append --cov=./ --cov-report=xml
}

function _test_multiproc {
    mkdir -p /tmp/test_multiproc
    export prometheus_multiproc_dir=/tmp/test_multiproc
    poetry run pytest -k test_multiprocess --cov-append --cov=./ --cov-report=xml
    rm -rf /tmp/test_multiproc
    unset prometheus_multiproc_dir
}

function _test {
    _test_not_slow
    _test_slow
    _test_multiproc
}

# ==============================================================================

function _help {
    cat << EOF
Functions you can use like this 'bash run.sh <function name>':
    docs
    lint
    requirements
    format-style
    format-imports
    format
    test-not-slow
    test-slow
    test-multiproc
    test
EOF
}

if [[ $# -eq 0 ]]
then
    _help
fi

for arg in "$@"
do
    if  [ $arg = "help" ] || [ $arg = "-help" ] || [ $arg = "--help" ]; then _help
    elif [ $arg = "docs" ]; then _docs
    elif [ $arg = "lint" ]; then _lint
    elif [ $arg = "requirements" ]; then _requirements
    elif [ $arg = "format-style" ]; then _format_style
    elif [ $arg = "format-imports" ]; then _format_imports
    elif [ $arg = "format" ]; then _format
    elif [ $arg = "test-not-slow" ]; then _test_not_slow
    elif [ $arg = "test-slow" ]; then _test_slow
    elif [ $arg = "test-multiproc" ]; then _test_multiproc
    elif [ $arg = "test" ]; then _test
    else _help
    fi
done
