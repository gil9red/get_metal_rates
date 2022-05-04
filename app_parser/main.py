#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import time

import db

from root_common import get_logger
from app_parser.parser import get_metal_rates, get_pair_dates
from app_parser.config import DIR_LOGS, TIMEOUT


log = get_logger(__file__, DIR_LOGS / 'log.txt')


while True:
    log.info("Запуск")
    try:
        start_date = db.MetalRate.get_last_date()
        log.info(f"Поиск от {start_date}\n")

        metal_rate_count = db.MetalRate.count()

        i = 0
        for date_req1, date_req2 in get_pair_dates(start_date):
            log.info(f'Поиск за {date_req1} - {date_req2}')

            while True:
                try:
                    rates = get_metal_rates(date_req1, date_req2)

                    log.info(f'Найдено {len(rates)} записей из API')
                    for metal_rate in rates:
                        db.MetalRate.add_from(metal_rate)

                except Exception:
                    log.exception('Ошибка:')
                    time.sleep(3600 * 4)  # Wait 4 hours
                    continue

                break

            if i > 0:
                time.sleep(60)

            i += 1

        diff_count = db.MetalRate.count() - metal_rate_count
        log.info(f'Добавлено записей: {diff_count}' if diff_count else 'Новый записей нет')

    except Exception:
        log.exception('Ошибка:')
        time.sleep(60 * 5)
        continue

    log.info("Завершено.\n")

    time.sleep(TIMEOUT)
