# https://just.systems/
set dotenv-load := false

@_default:
    just --list

@build:
    pipenv run python3 -m build

@pypi:
    pipenv run twine upload dist/*

@publish: build pypi

@docs:
    cd docs && make html

@test:
    pipenv install
    pipenv install -e .
    pipenv run bash -c "cd test && ./manage.py test"
