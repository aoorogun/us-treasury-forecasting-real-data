.PHONY: install download train evaluate scenario monitor test lint all

install:
	pip install -e ".[dev]"

download:
	treasury-forecast download

train:
	treasury-forecast train

evaluate:
	treasury-forecast evaluate

scenario:
	treasury-forecast scenario --file configs/scenario_rate_shock.json

monitor:
	treasury-forecast monitor

test:
	python -m unittest discover -s tests -v

lint:
	ruff check src tests scripts sagemaker

all: download train evaluate scenario monitor test
