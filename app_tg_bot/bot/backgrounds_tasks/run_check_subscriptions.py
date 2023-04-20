#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import time

from telegram import Bot, ParseMode

from app_tg_bot.bot.common import caller_name, get_logger
from app_tg_bot.config import TOKEN, DIR_LOGS
from db import Subscription, MetalRate


log = get_logger(__file__, DIR_LOGS / "notifications.txt")


def sending_notifications():
    prefix = f"[{caller_name()}]"

    bot = Bot(TOKEN)

    log.info(f"{prefix} Запуск")
    log.debug(f"{prefix} Имя бота {bot.first_name!r} ({bot.name})")

    while True:
        try:
            subscriptions = Subscription.get_active_unsent_subscriptions()
            if not subscriptions:
                continue

            log.info(
                f"{prefix} Выполняется рассылка к {len(subscriptions)} пользователям"
            )

            text = f"<b>Рассылка</b>\n{MetalRate.get_last().get_description(show_diff=True)}"
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
            log.exception(f"{prefix} Ошибка:")
            time.sleep(60)

        finally:
            time.sleep(1)

    log.info(f"{prefix} Завершение")
