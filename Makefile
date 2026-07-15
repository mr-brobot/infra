.PHONY: format check ci

format:
	uv run --group dev ruff format .

check:
	uv run --group dev ruff check .
	uv run --group dev pyrefly check .

ci: format check
