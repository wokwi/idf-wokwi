# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, CodeMagic LTD

"""Interactive mode - forward stdin to simulation, platform-aware."""

from __future__ import annotations

import sys

from wokwi_client import WokwiClientSync

from ._log import yellow_print

if sys.platform == "win32":
    import msvcrt

    def _platform_loop(client: WokwiClientSync) -> None:
        try:
            while True:
                ch = msvcrt.getch()
                if ch == b"\x1d":  # Ctrl+]
                    break
                client.serial_write(ch)
        except OSError:
            pass

else:
    import os
    import termios
    import tty

    def _platform_loop(client: WokwiClientSync) -> None:
        stdin_fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(stdin_fd)
        try:
            tty.setcbreak(stdin_fd)
            while True:
                ch = os.read(stdin_fd, 1)
                if ch == b"\x1d":  # Ctrl+]
                    break
                client.serial_write(ch)
        except OSError:
            pass
        finally:
            termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)


def interactive_loop(client: WokwiClientSync) -> None:
    yellow_print("Press Ctrl+] to stop the simulation")
    _platform_loop(client)
