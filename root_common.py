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


class SubscriptionResultEnum(enum.Enum):
    SUBSCRIBE_OK = enum.auto()
    UNSUBSCRIBE_OK = enum.auto()
    ALREADY = enum.auto()
