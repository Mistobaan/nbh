lint:
	uv run pre-commit run --all

build:
	uv build --sdist --wheel

test:
	uv run python -m unittest discover tests

render:
	uv run nbh ./tests/fixtures/simple.ipynb --output /tmp/

publish_to_test_pypi:
	rm -fr ./dist
	rm -fr ./build
	uv build --sdist --wheel
	uvx twine upload --repository testpypi dist/*

bump_version_patch:
	uv version --bump patch
	git add .
	git commit -m "Bump version to $(shell uv version)"


publish_to_pypi:
	rm -fr ./dist
	rm -fr ./build
	uv build --sdist --wheel
	uvx twine upload dist/*
