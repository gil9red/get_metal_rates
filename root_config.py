#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


from pathlib import Path


# Текущая папка, где находится скрипт
ROOT_DIR: Path = Path(__file__).resolve().parent

DIR_LOGS: Path = ROOT_DIR / 'logs'
DIR_LOGS.mkdir(parents=True, exist_ok=True)

# Создание папки для базы данных
DB_DIR_NAME: Path = ROOT_DIR / 'database'
DB_DIR_NAME.mkdir(parents=True, exist_ok=True)

# Путь к файлу базы данных
DB_FILE_NAME: str = str(DB_DIR_NAME / 'database.sqlite')

ITEMS_PER_PAGE: int = 10