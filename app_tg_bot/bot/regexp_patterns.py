#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import re
from app_tg_bot.bot.third_party.regexp import fill_string_pattern


PATTERN_REPLY_ADMIN_STATS = re.compile(
    r"^admin[ _]stats$|^статистика[ _]админа$", flags=re.IGNORECASE
)
COMMAND_ADMIN_STATS = "admin_stats"

PATTERN_REPLY_GET_AS_TEXT = re.compile(r"^Последняя запись$", flags=re.IGNORECASE)
PATTERN_INLINE_GET_BY_DATE = re.compile(r"^get_by_date=(.+)$")

PATTERN_REPLY_SELECT_DATE = re.compile(r"^Выбрать дату", flags=re.IGNORECASE)
PATTERN_INLINE_SELECT_DATE = re.compile(r".+;\d+;\d+;\d+")  # NOTE: Формат telegramcalendar.py

PATTERN_REPLY_GET_LAST_7_AS_CHART = re.compile(r"^График за 7$", flags=re.IGNORECASE)
PATTERN_REPLY_GET_LAST_31_AS_CHART = re.compile(r"^График за 31$", flags=re.IGNORECASE)
PATTERN_REPLY_GET_ALL_AS_CHART = re.compile(
    r"^График за все данные$", flags=re.IGNORECASE
)
PATTERN_INLINE_GET_AS_CHART = re.compile(r"^get_last_(.+)_as_chart=(.+)$")

PATTERN_INLINE_GET_CHART_METAL_BY_YEAR = re.compile(r"^get_chart metal=(.+) year=(.+)$")

PATTERN_REPLY_SUBSCRIBE = re.compile(r"^Подписаться$", flags=re.IGNORECASE)
PATTERN_REPLY_UNSUBSCRIBE = re.compile(r"^Отписаться$", flags=re.IGNORECASE)

CALLBACK_IGNORE = "IGNORE"


if __name__ == "__main__":
    import datetime as DT

    assert (
        fill_string_pattern(PATTERN_INLINE_GET_BY_DATE, DT.date(2022, 4, 1))
        == "get_by_date=2022-04-01"
    )
    assert fill_string_pattern(PATTERN_REPLY_GET_AS_TEXT) == "Последняя запись"

    assert (
        fill_string_pattern(PATTERN_INLINE_GET_AS_CHART, -1, "gold")
        == "get_last_-1_as_chart=gold"
    )
    assert (
        fill_string_pattern(PATTERN_INLINE_GET_AS_CHART, 31, "gold")
        == "get_last_31_as_chart=gold"
    )

    m = PATTERN_INLINE_GET_AS_CHART.match(
        fill_string_pattern(PATTERN_INLINE_GET_AS_CHART, 31, "gold")
    )
    assert m.re == PATTERN_INLINE_GET_AS_CHART
    assert m.re.pattern == PATTERN_INLINE_GET_AS_CHART.pattern
    assert m.groups() == ("31", "gold")
