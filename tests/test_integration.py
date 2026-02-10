# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, CodeMagic LTD

from __future__ import annotations

import os
import threading
from typing import Any
from unittest.mock import MagicMock

import pytest

from idf_wokwi.wokwi_ext import TIMEOUT_EXIT_CODE, action_extensions, wokwi_callback


def _hello_world_build_dir() -> str:
    """Return path to a pre-built hello_world build directory.

    Set BUILD_DIR env var to override.
    """
    explicit = os.environ.get("BUILD_DIR")
    if explicit:
        assert os.path.isfile(os.path.join(explicit, "flasher_args.json")), (
            f"BUILD_DIR={explicit} does not contain flasher_args.json"
        )
        return explicit

    idf_path = os.environ.get("IDF_PATH", "/workspace/esp-idf")
    candidates = [
        os.path.join(idf_path, "examples", "get-started", "hello_world", "build"),
    ]
    for c in candidates:
        if os.path.isfile(os.path.join(c, "flasher_args.json")):
            return c
    pytest.fail("No hello_world build directory with flasher_args.json found")
    raise AssertionError  # unreachable, helps mypy


def test_action_extensions_structure() -> None:
    result = action_extensions({}, "/tmp")
    assert result["version"] == "1"
    assert "wokwi" in result["actions"]
    assert callable(result["actions"]["wokwi"]["callback"])
    assert result["actions"]["wokwi"]["dependencies"] == ["all"]


class TestWokwiIntegration:
    """Integration tests that connect to a real Wokwi CI server."""

    def _make_args(self, build_dir: str) -> Any:
        mock = MagicMock()
        mock.build_dir = build_dir
        return mock

    def _run_callback_in_thread(
        self,
        build_dir: str,
        *,
        timeout: int = 10000,
        expect_text: str = "",
        fail_text: str = "",
        expect_regex: str = "",
        fail_regex: str = "",
        diagram_file: str = "",
    ) -> int:
        """Run wokwi_callback in a thread and return the exit code (0=success)."""
        exit_code = 0

        def _target() -> None:
            nonlocal exit_code
            try:
                wokwi_callback(
                    action="wokwi",
                    ctx=None,
                    args=self._make_args(build_dir),
                    diagram_file=diagram_file,
                    timeout=timeout,
                    expect_text=expect_text,
                    fail_text=fail_text,
                    expect_regex=expect_regex,
                    fail_regex=fail_regex,
                )
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else 1

        t = threading.Thread(target=_target)
        t.start()
        t.join(timeout=30)
        if t.is_alive():
            exit_code = -1
        return exit_code

    def test_expect_text_hello_world(self) -> None:
        """Simulation should find 'Hello world' in serial output."""
        build_dir = _hello_world_build_dir()
        code = self._run_callback_in_thread(build_dir, timeout=15000, expect_text="Hello world")
        assert code == 0

    def test_timeout_returns_42(self) -> None:
        """A very short timeout should exit with code 42."""
        build_dir = _hello_world_build_dir()
        code = self._run_callback_in_thread(
            build_dir, timeout=1, expect_text="this_text_will_never_appear"
        )
        assert code == TIMEOUT_EXIT_CODE

    def test_fail_text(self) -> None:
        """fail-text should cause exit code 1."""
        build_dir = _hello_world_build_dir()
        # "rst:0x1" appears early in ESP32 boot output
        code = self._run_callback_in_thread(build_dir, timeout=15000, fail_text="rst:0x1")
        assert code == 1

    def test_expect_regex(self) -> None:
        """expect-regex should match serial output with a pattern."""
        build_dir = _hello_world_build_dir()
        code = self._run_callback_in_thread(build_dir, timeout=15000, expect_regex=r"Hello\s+world")
        assert code == 0

    def test_fail_regex(self) -> None:
        """fail-regex should cause exit code 1 on pattern match."""
        build_dir = _hello_world_build_dir()
        code = self._run_callback_in_thread(build_dir, timeout=15000, fail_regex=r"rst:0x[0-9a-f]+")
        assert code == 1
