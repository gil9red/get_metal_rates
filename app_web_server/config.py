#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from pathlib import Path


DIR: Path = Path(__file__).resolve().parent

DIR_LOGS: Path = DIR / "logs"
DIR_LOGS.mkdir(parents=True, exist_ok=True)

PORT_WEB: int = 12000
