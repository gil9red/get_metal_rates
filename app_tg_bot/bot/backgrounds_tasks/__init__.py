#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


from threading import Thread

from app_tg_bot.bot.backgrounds_tasks.check_new_metal_rates import check_new_metal_rates
from app_tg_bot.bot.backgrounds_tasks.run_check_subscriptions import sending_notifications


def run():
    Thread(target=check_new_metal_rates).start()
    Thread(target=sending_notifications).start()
