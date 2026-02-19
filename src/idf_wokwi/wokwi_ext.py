# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2026, CodeMagic LTD

"""
ESP-IDF extension that adds ``idf.py wokwi`` for running Wokwi simulations.

Install once with ``pip install idf-wokwi`` and the command is available in
every ESP-IDF project.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from wokwi_client import GET_TOKEN_URL, IdfFirmwareUploadResult, WokwiClientSync

from ._log import red_print, yellow_print
from .diagram import find_diagram, generate_diagram
from .expect_engine import TIMEOUT_EXIT_CODE, ExpectEngine
from .interactive import interactive_loop

__all__ = ["TIMEOUT_EXIT_CODE", "action_extensions", "wokwi_callback"]


def _get_project_desc(build_dir: str) -> dict[str, Any]:
    desc_path = os.path.join(build_dir, "project_description.json")
    if not os.path.exists(desc_path):
        red_print(f"Project description not found: {desc_path}")
        red_print("Please build the project first with: idf.py build")
        raise SystemExit(1)
    with open(desc_path, encoding="utf-8") as f:
        project_desc: dict[str, Any] = json.load(f)
    return project_desc


def _upload_artifacts(
    client: WokwiClientSync,
    project_desc: dict[str, Any],
    build_dir: str,
    diagram_path: str,
    flasher_args_path: str,
    elf_path: str,
) -> tuple[IdfFirmwareUploadResult, str]:
    """Upload diagram, firmware, and ELF to the simulator. Returns (idf_result, elf_name)."""
    if diagram_path:
        client.upload_file("diagram.json", Path(diagram_path))
        yellow_print(f"Uploaded diagram: {diagram_path}")
    else:
        target: str = project_desc.get("target", "esp32")
        diagram_content = generate_diagram(target)
        client.upload("diagram.json", diagram_content.encode("utf-8"))
        yellow_print(f"Generated diagram for target: {target}")

    idf = client.upload_idf_firmware(flasher_args_path)
    yellow_print("Uploaded firmware")

    elf_name = ""
    if elf_path and os.path.exists(elf_path):
        elf_name = client.upload_file(os.path.basename(elf_path), Path(elf_path))
        yellow_print(f"Uploaded ELF: {os.path.basename(elf_path)}")

    return idf, elf_name


def wokwi_callback(
    action: str,
    ctx: Any,
    args: Any,
    diagram_file: str,
    timeout: int,
    expect_text: str,
    fail_text: str,
    expect_regex: str,
    fail_regex: str,
) -> None:
    token = os.environ.get("WOKWI_CLI_TOKEN", "")
    if not token:
        red_print("WOKWI_CLI_TOKEN environment variable is not set.")
        red_print(f"Get your token at: {GET_TOKEN_URL}")
        raise SystemExit(1)

    build_dir: str = args.build_dir
    project_desc = _get_project_desc(build_dir)
    project_path: str = project_desc.get("project_path", os.getcwd())

    flasher_args_path = os.path.join(build_dir, "flasher_args.json")
    if not os.path.exists(flasher_args_path):
        red_print(f"flasher_args.json not found in {build_dir}")
        red_print("Please build the project first with: idf.py build")
        raise SystemExit(1)

    elf_path = project_desc.get("app_elf", "")
    if elf_path and not os.path.isabs(elf_path):
        elf_path = os.path.join(build_dir, elf_path)

    diagram_path = find_diagram(project_path, diagram_file)

    server = os.environ.get("WOKWI_CLI_SERVER")
    client = WokwiClientSync(token, server=server)

    try:
        hello = client.connect()
        yellow_print(f"Connected to Wokwi Simulator (server {hello.get('version', '?')})")

        idf, elf_name = _upload_artifacts(
            client, project_desc, build_dir, diagram_path, flasher_args_path, elf_path
        )

        engine = ExpectEngine(expect_text, fail_text, expect_regex, fail_regex)
        client.serial_monitor(engine.feed)

        client.start_simulation(
            firmware=idf.firmware, flash_size=idf.flash_size, elf=elf_name or None
        )
        yellow_print("Simulation started")

        if engine.active or timeout:
            engine.wait(timeout)
        else:
            interactive_loop(client)

    finally:
        try:
            client.disconnect()
        except Exception:
            pass


def action_extensions(base_actions: dict[str, Any], project_path: str) -> dict[str, Any]:
    return {
        "version": "1",
        "actions": {
            "wokwi": {
                "callback": wokwi_callback,
                "help": "Run Wokwi simulation.",
                "dependencies": ["all"],
                "options": [
                    {
                        "names": ["--diagram-file"],
                        "help": (
                            "Path to diagram.json file. "
                            "If not specified, looks for diagram.json in the project root."
                        ),
                        "is_flag": False,
                        "default": "",
                    },
                    {
                        "names": ["--timeout"],
                        "help": (
                            "Simulation timeout in milliseconds. "
                            "Exits with code 42 on timeout. 0 means no timeout."
                        ),
                        "is_flag": False,
                        "default": 0,
                        "type": int,
                    },
                    {
                        "names": ["--expect-text"],
                        "help": "Exit successfully when this text appears in serial output.",
                        "is_flag": False,
                        "default": "",
                    },
                    {
                        "names": ["--fail-text"],
                        "help": "Exit with error when this text appears in serial output.",
                        "is_flag": False,
                        "default": "",
                    },
                    {
                        "names": ["--expect-regex"],
                        "help": "Exit successfully when this regex matches a serial output line.",
                        "is_flag": False,
                        "default": "",
                    },
                    {
                        "names": ["--fail-regex"],
                        "help": "Exit with error when this regex matches a serial output line.",
                        "is_flag": False,
                        "default": "",
                    },
                ],
            }
        },
    }
