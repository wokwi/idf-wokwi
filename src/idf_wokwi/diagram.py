# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, Wokwi B.V.

"""Diagram generation and discovery for Wokwi simulations."""

from __future__ import annotations

import json
import os
from typing import NamedTuple

from ._log import red_print


class Board(NamedTuple):
    part: str
    tx: str = "TX"
    rx: str = "RX"


# Mirrors the board table in wokwi-cli (packages/cli/src/project/boards.ts).
TARGET_BOARDS: dict[str, Board] = {
    "esp32": Board("board-esp32-devkit-c-v4"),
    "esp32s2": Board("board-esp32-s2-devkitm-1"),
    "esp32s3": Board("board-esp32-s3-devkitc-1"),
    "esp32c3": Board("board-esp32-c3-devkitm-1"),
    "esp32c5": Board("board-esp32-c5-devkitc-1"),
    "esp32c6": Board("board-esp32-c6-devkitc-1"),
    "esp32c61": Board("board-esp32-c61-devkitc-1"),
    "esp32h2": Board("board-esp32-h2-devkitm-1"),
    "esp32p4": Board("board-esp32-p4-function-ev", tx="37", rx="38"),
    "esp32s31": Board("board-esp32-s31-function-coreboard-1", tx="TX0", rx="RX0"),
}


def generate_diagram(target: str) -> str:
    """Return a minimal diagram.json string for the given target."""
    if target not in TARGET_BOARDS:
        red_print(f"No Wokwi board for target {target}; add a diagram.json to the project.")
        red_print(f"Targets with a generated diagram: {', '.join(TARGET_BOARDS)}")
        raise SystemExit(1)
    board = TARGET_BOARDS[target]
    diagram = {
        "version": 1,
        "author": "idf-wokwi",
        "editor": "wokwi",
        "parts": [{"type": board.part, "id": "esp"}],
        "connections": [
            [f"esp:{board.tx}", "$serialMonitor:RX", "", []],
            [f"esp:{board.rx}", "$serialMonitor:TX", "", []],
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
