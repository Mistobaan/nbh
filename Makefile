lint:
	uv run pre-commit run --all

build:
	uv build --sdist --wheel

test:
	uv run python -m unittest discover tests

render:
	uv run nbh ./tests/fixtures/simple.ipynb --output /tmp/

publish_to_test_pypi: build
	uvx twine upload --repository testpypi dist/*

bump_version_patch:
	uv version --bump patch
