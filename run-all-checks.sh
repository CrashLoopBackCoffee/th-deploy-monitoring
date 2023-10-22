#!/usr/bin/env bash

set -x
set -eu

black .
flake8
pylint $(git ls-files '*.py')
