#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import enum
import logging
import sys

from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union

from root_config import DATE_FORMAT


def get_logger(
        name: str,
        file: Union[str, Path] = 'log.txt',
        encoding='utf-8',
        log_stdout=True,
        log_file=True
) -> 'logging.Logger':
    log = logging.getLogger(name)

    # Возвращаем уже существующий логгер
    if log.handlers:
        return log

    log.setLevel(logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-8s %(message)s')

    if log_file:
        fh = RotatingFileHandler(file, maxBytes=10000000, backupCount=5, encoding=encoding)
        fh.setFormatter(formatter)
        log.addHandler(fh)

    if log_stdout:
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setFormatter(formatter)
        log.addHandler(sh)

    return log


def get_date_str(date: DT.date) -> str:
    return date.strftime(DATE_FORMAT)


def get_start_date(year: int) -> DT.date:
    return DT.date(year, 1, 1)


def get_end_date(year: int) -> DT.date:
    return DT.date(year + 1, 1, 1) - DT.timedelta(days=1)


class SubscriptionResultEnum(enum.Enum):
    SUBSCRIBE_OK = enum.auto()
    UNSUBSCRIBE_OK = enum.auto()
    ALREADY = enum.auto()


class MetalEnum(enum.Enum):
    GOLD = ('золото', 'золота', '#FFA500')
    SILVER = ('серебро', 'серебра', '#898989')
    PLATINUM = ('платина', 'платины', '#86B066')
    PALLADIUM = ('палладий', 'палладия', '#617DB4')

    def __init__(self, singular: str, plural: str, color: str):
        self.name_lower = self.name.lower()
        self.singular = singular
        self.plural = plural
        self.color = color


DEFAULT_METAL = MetalEnum.GOLD
