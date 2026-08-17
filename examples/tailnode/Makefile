.PHONY: format check ci deploy create stop terminate destroy

format:
	uv run --group dev ruff format .

check:
	uv run --group dev ruff check --fix .
	uv run --group dev pyrefly check .

ci: format check

deploy:
	scripts/deploy.sh

create:
	mutagen project create

start:
	mutagen project start

stop:
	mutagen project stop

terminate:
	mutagen project terminate

destroy:
	scripts/destroy.sh
