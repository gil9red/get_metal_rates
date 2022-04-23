#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import logging
import os
import time

from threading import Thread
from typing import Optional

# pip install python-telegram-bot
from telegram import Bot, ParseMode
from telegram.ext import Updater, Defaults

from bot import commands
from bot.common import caller_name, log
from config import TOKEN
from db import Subscription, Settings, MetalRate


DATA = {
    'BOT': None,
}


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
        try:
            bot: Optional[Bot] = DATA.get('bot')
            if not bot:
                continue

            subscriptions = Subscription.get_active_unsent_subscriptions()
            if not subscriptions:
                continue

            text = f'<b>Рассылка</b>\n{MetalRate.get_last().get_description(show_diff=True)}'
            for subscription in subscriptions:
                bot.send_message(
                    chat_id=subscription.user_id,  # Для приватных чатов chat_id равен user_id
                    text=text,
                    parse_mode=ParseMode.HTML,
                )

                subscription.was_sending = True
                subscription.save()

                time.sleep(0.4)

        except Exception:
            log.exception(f'{prefix} Ошибка:')
            time.sleep(60)

        finally:
            time.sleep(1)


def main():
    log.debug('Start')

    cpu_count = os.cpu_count()
    workers = cpu_count
    log.debug(f'System: CPU_COUNT={cpu_count}, WORKERS={workers}')

    updater = Updater(
        TOKEN,
        workers=workers,
        defaults=Defaults(run_async=True),
    )
    bot = updater.bot
    log.debug(f'Bot name {bot.first_name!r} ({bot.name})')

    DATA['bot'] = bot

    dp = updater.dispatcher
    commands.setup(dp)

    updater.start_polling()
    updater.idle()

    log.debug('Finish')


if __name__ == '__main__':
    Thread(target=check_new_metal_rates, args=[log]).start()
    Thread(target=sending_notifications, args=[log]).start()

    while True:
        try:
            main()
        except:
            log.exception('')

            timeout = 15
            log.info(f'Restarting the bot after {timeout} seconds')
            time.sleep(timeout)
