# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, CodeMagic LTD

"""Line-based serial text/regex matcher"""

from __future__ import annotations

import re
import threading
import time

from ._log import red_print, yellow_print

TIMEOUT_EXIT_CODE = 42

_MAX_LINE_LENGTH = 10_000


class ExpectEngine:
    """Buffer chars until newline, then test the complete line against patterns."""

    def __init__(
        self,
        expect_text: str = "",
        fail_text: str = "",
        expect_regex: str = "",
        fail_regex: str = "",
    ) -> None:
        self.expect_text = expect_text
        self.fail_text = fail_text
        self._expect_re = re.compile(expect_regex) if expect_regex else None
        self._fail_re = re.compile(fail_regex) if fail_regex else None
        self.match_event = threading.Event()
        self.fail_event = threading.Event()
        self.active = bool(expect_text or fail_text or self._expect_re or self._fail_re)
        self._current_line: list[str] = []

    def _test_line(self, line: str) -> None:
        if self.expect_text and self.expect_text in line:
            self.match_event.set()
        if self._expect_re and self._expect_re.search(line):
            self.match_event.set()
        if self.fail_text and self.fail_text in line:
            self.fail_event.set()
        if self._fail_re and self._fail_re.search(line):
            self.fail_event.set()

    def feed(self, data: bytes) -> None:
        """Feed raw serial bytes - prints to stdout and tests for pattern matches."""
        text = data.decode("utf-8", errors="replace")
        print(text, end="", flush=True)

        if not self.active:
            return

        for ch in text:
            if ch == "\n":
                self._test_line("".join(self._current_line))
                self._current_line.clear()
            elif len(self._current_line) < _MAX_LINE_LENGTH:
                self._current_line.append(ch)

    def wait(self, timeout_ms: int) -> None:
        """Block until a match/fail is found or timeout elapses. Raises SystemExit."""
        deadline = time.monotonic() + timeout_ms / 1000.0 if timeout_ms else float("inf")

        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                red_print(f"Timeout after {timeout_ms} ms")
                raise SystemExit(TIMEOUT_EXIT_CODE)

            if self.fail_event.is_set():
                msg = self.fail_text or str(self._fail_re and self._fail_re.pattern)
                red_print(f"Fail text detected: {msg}")
                raise SystemExit(1)

            if self.match_event.is_set():
                msg = self.expect_text or str(self._expect_re and self._expect_re.pattern)
                yellow_print(f"Expected text found: {msg}")
                return

            time.sleep(min(remaining, 0.1))
