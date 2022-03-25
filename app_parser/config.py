#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
from pathlib import Path


# Текущая папка, где находится скрипт
DIR = Path(__file__).resolve().parent


FILE_COOKIES: Path = DIR / 'cookies.txt'
START_DATE: DT.date = DT.date(year=2000, month=1, day=1)
