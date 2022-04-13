#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import logging
import time

from threading import Thread

from app_tg_bot.bot import common
from app_tg_bot.bot.common import caller_name, log
from db import Subscription, Settings, MetalRate


def check_new_metal_rates(log: logging.Logger):
    prefix = f'[{caller_name()}]'

    while True:
        try:
            settings_last_date = Settings.get_last_date_of_metals_rate()
            current_last_date = MetalRate.get_last_date()
            if settings_last_date == current_last_date:
                continue

            log.info(f'{prefix} Дата поменялась {settings_last_date} -> {current_last_date}')
            Settings.set_last_date_of_metals_rate(current_last_date)
            Subscription.update(was_sending=False).execute()

        except Exception:
            log.exception(f'{prefix} Ошибка:')

        finally:
            time.sleep(60)


def sending_notifications(log: logging.Logger):
    prefix = f'[{caller_name()}]'

    while True:
        if not common.BOT:
            continue

        try:
            text = MetalRate.get_last().get_description()

            for subscription in Subscription.get_active_unsent_subscriptions():
                common.BOT.send_message(
                    chat_id=subscription.user_id,  # Для приватных чатов chat_id равен user_id
                    text=text,
                )

                subscription.was_sending = True
                subscription.save()

                time.sleep(0.4)

        except Exception:
            log.exception(f'{prefix} Ошибка:')
            time.sleep(60)

        finally:
            time.sleep(1)


def run():
    Thread(target=check_new_metal_rates, args=[log]).start()
    Thread(target=sending_notifications, args=[log]).start()
