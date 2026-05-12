#!/usr/bin/env python3
# logging.py - Unified logging for dev-flow commands
#
# Provides colored console output functions used across all commands.

import sys


def log_info(msg: str) -> None:
    print(f"\033[0;34m[INFO]\033[0m {msg}")


def log_success(msg: str) -> None:
    print(f"\033[0;32m[OK]\033[0m {msg}")


def log_error(msg: str, file=None) -> None:
    print(f"\033[0;31m[ERROR]\033[0m {msg}", file=file or sys.stderr)


def log_warn(msg: str) -> None:
    print(f"\033[0;33m[WARN]\033[0m {msg}")


def log_step(msg: str) -> None:
    print(f"\033[0;36m[STEP]\033[0m {msg}")
