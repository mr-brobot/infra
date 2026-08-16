.PHONY: format check ci

format:
	uv run --group dev ruff format .

check:
	uv run --group dev ruff check --fix .
	uv run --group dev pyrefly check .

ci: format check
