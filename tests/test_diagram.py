# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, Wokwi B.V.

from __future__ import annotations

import json

import pytest

from idf_wokwi.diagram import generate_diagram


def _connections(target: str) -> list[list[str]]:
    connections: list[list[str]] = json.loads(generate_diagram(target))["connections"]
    return connections


def test_default_serial_pins() -> None:
    diagram = json.loads(generate_diagram("esp32s3"))
    assert diagram["parts"] == [{"type": "board-esp32-s3-devkitc-1", "id": "esp"}]
    assert diagram["connections"] == [
        ["esp:TX", "$serialMonitor:RX", "", []],
        ["esp:RX", "$serialMonitor:TX", "", []],
    ]


@pytest.mark.parametrize(
    ("target", "tx", "rx"),
    [("esp32p4", "esp:37", "esp:38"), ("esp32s31", "esp:TX0", "esp:RX0")],
)
def test_board_specific_serial_pins(target: str, tx: str, rx: str) -> None:
    connections = _connections(target)
    assert connections[0][0] == tx
    assert connections[1][0] == rx


def test_unknown_target_exits() -> None:
    with pytest.raises(SystemExit) as exc:
        generate_diagram("esp32xx")
    assert exc.value.code == 1
