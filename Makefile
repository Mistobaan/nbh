lint:
	uv run pre-commit run --all

build:
	uv build --sdist --wheel

test:
	uv run python -m unittest discover tests

render:
	uv run nbh ./tests/fixtures/simple.ipynb --output /tmp/
