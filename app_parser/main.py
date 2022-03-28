#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import time

import db

from root_common import log
from app_parser.parser import get_metal_rates, get_pair_dates


while True:
    log.info("Запуск")
    try:
        start_date = db.MetalRate.get_last_date()
        log.info(f"Поиск от {start_date}\n")

        metal_rate_count = db.MetalRate.count()

        for date_req1, date_req2 in get_pair_dates(start_date):
            log.info(f'Поиск за {date_req1} - {date_req2}')

            while True:
                try:
                    rates = get_metal_rates(date_req1, date_req2)

                    log.info(f'Найдено {len(rates)} записей из API')
                    if not rates:
                        log.info('Ничего не вернулось, похоже на ошибку сервиса. Нужно повторить')
                        time.sleep(60)
                        continue

                    for metal_rate in rates:
                        db.MetalRate.add_from(metal_rate)

                except Exception:
                    log.exception('Ошибка:')
                    time.sleep(3600 * 4)  # Wait 4 hours
                    continue

                break

            time.sleep(60)

        diff_count = db.MetalRate.count() - metal_rate_count
        log.info(f'Добавлено записей: {diff_count}' if diff_count else 'Новый записей нет')

    except Exception:
        log.exception('Ошибка:')
        time.sleep(60 * 5)
        continue

    log.info("Завершено.\n")

    time.sleep(3600 * 8)
