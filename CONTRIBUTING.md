# Contributing

## Setup

```bash
pip install hatch
```

## Development

Lint and type-check:

```bash
hatch run ruff format --check .
hatch run ruff check .
hatch run mypy .
```

Run tests:

```bash
hatch run dev:pytest
```

## Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```
