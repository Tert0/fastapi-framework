#!/bin/sh

if coverage run --source=fastapi_framework -m unittest discover -v tests
then
    coverage ${1:-xml}
    coverage report
    coverage erase
else
    coverage erase
    exit 1
fi