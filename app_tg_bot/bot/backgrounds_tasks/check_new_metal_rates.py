#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time

from app_tg_bot.config import DIR_LOGS
from app_tg_bot.bot.common import caller_name, get_logger
from db import Settings, MetalRate, Subscription


log = get_logger(__file__, DIR_LOGS / "parser.txt")


def check_new_metal_rates():
    prefix = f"[{caller_name()}]"

    log.info(f"{prefix} Запуск")

    while True:
        try:
            settings_last_date = Settings.get_last_date_of_metals_rate()
            current_last_date = MetalRate.get_last_date()
            if settings_last_date == current_last_date:
                continue

            log.info(
                f"{prefix} Дата поменялась {settings_last_date} -> {current_last_date}"
            )
            Settings.set_last_date_of_metals_rate(current_last_date)
            Subscription.update(was_sending=False).execute()

        except Exception:
            log.exception(f"{prefix} Ошибка:")

        finally:
            time.sleep(60)

    log.info(f"{prefix} Завершение")
