# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, CodeMagic LTD

from __future__ import annotations

import sys


def red_print(msg: str) -> None:
    print(f"\033[31m{msg}\033[0m", file=sys.stderr)


def yellow_print(msg: str) -> None:
    print(f"\033[33m{msg}\033[0m", file=sys.stderr)
