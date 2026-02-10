# idf-wokwi

Wokwi simulation extension for ESP-IDF. Adds `idf.py wokwi` command.

## Installation

```bash
pip install idf-wokwi
```

## Usage

Set `WOKWI_CLI_TOKEN` to your [Wokwi API token](https://wokwi.com/dashboard/ci?utm_source=idf-wokwi).

```bash
export WOKWI_CLI_TOKEN="your-token-here"

# Build and simulate
idf.py build
idf.py wokwi

# CI mode: exit when expected text appears
idf.py wokwi --timeout 10000 --expect-text "Hello world!"
```

## Options

| Option           | Description                                                    |
| ---------------- | -------------------------------------------------------------- |
| `--diagram-file` | Path to `diagram.json` (defaults to project root)              |
| `--timeout`      | Simulation timeout in milliseconds (exit code 42 on timeout)   |
| `--expect-text`  | Exit successfully when this text appears in serial output      |
| `--fail-text`    | Exit with error when this text appears in serial output        |
| `--expect-regex` | Exit successfully when this regex matches a serial output line |
| `--fail-regex`   | Exit with error when this regex matches a serial output line   |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
