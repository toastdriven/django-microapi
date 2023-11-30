# https://just.systems/
set dotenv-load := false

@_default:
    just --list

@build:
    pipenv run python3 -m build

@pypi:
    pipenv run twine upload dist/*

@publish: build pypi
