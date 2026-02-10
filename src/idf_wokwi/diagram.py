# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, CodeMagic LTD

"""Diagram generation and discovery for Wokwi simulations."""

from __future__ import annotations

import json
import os

from ._log import red_print

TARGET_WOKWI_PARTS: dict[str, str] = {
    "esp32": "board-esp32-devkit-c-v4",
    "esp32s2": "board-esp32-s2-devkitm-1",
    "esp32s3": "board-esp32-s3-devkitc-1",
    "esp32c3": "board-esp32-c3-devkitm-1",
    "esp32c5": "board-esp32-c5-devkitc-1",
    "esp32c6": "board-esp32-c6-devkitc-1",
    "esp32h2": "board-esp32-h2-devkitm-1",
    "esp32p4": "board-esp32-p4-function-ev",
}


def generate_diagram(target: str) -> str:
    """Return a minimal diagram.json string for the given target."""
    part_type = TARGET_WOKWI_PARTS.get(target, f"board-{target}-devkit")
    diagram = {
        "version": 1,
        "author": "idf-wokwi",
        "editor": "wokwi",
        "parts": [{"type": part_type, "id": "esp"}],
        "connections": [
            ["esp:TX", "$serialMonitor:RX", "", []],
            ["esp:RX", "$serialMonitor:TX", "", []],
        ],
        "serialMonitor": {"display": "terminal"},
    }
    return json.dumps(diagram)


def find_diagram(project_path: str, diagram_file: str) -> str:
    """Locate diagram.json - returns path or empty string if auto-generation needed."""
    if diagram_file:
        if not os.path.isabs(diagram_file):
            diagram_file = os.path.join(project_path, diagram_file)
        if not os.path.exists(diagram_file):
            red_print(f"Diagram file not found: {diagram_file}")
            raise SystemExit(1)
        return diagram_file

    default = os.path.join(project_path, "diagram.json")
    if os.path.exists(default):
        return default

    return ""
