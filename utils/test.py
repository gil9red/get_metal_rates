#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import random
import unittest

from io import BytesIO
from pathlib import Path
from uuid import uuid4

# pip install matplotlib
import matplotlib.dates as mdates

from peewee import SqliteDatabase

from db import MetalRate, Settings, Subscription, db
from root_common import SubscriptionResultEnum, MetalEnum
from utils.draw_plot import (
    draw_plot, get_plot_for_metal,
    get_plot_for_gold, get_plot_for_silver, get_plot_for_platinum, get_plot_for_palladium
)


DIR = Path(__file__).resolve().parent


# NOTE: https://docs.peewee-orm.com/en/latest/peewee/database.html#testing-peewee-applications
class TestCaseDB(unittest.TestCase):
    def setUp(self):
        self.models = [MetalRate, Subscription, Settings]
        self.test_db = SqliteDatabase(':memory:')
        self.test_db.bind(self.models, bind_refs=False, bind_backrefs=False)
        self.test_db.connect()
        self.test_db.create_tables(self.models)

    def tearDown(self):
        # Нужно вернуть маппинг к текущей базе данных, иначе следующие тесты, использующие базу данных, типа
        # рисования графиков будут проваливаться
        db.bind(self.models, bind_refs=False, bind_backrefs=False)

    def test_metalrate(self):
        self.assertEqual(MetalRate.get_last_dates(MetalRate.count()), MetalRate.get_last_dates(-1))
        self.assertEqual(MetalRate.get_last_dates(-1), MetalRate.get_last_dates())
        self.assertEqual(MetalRate.get_last_date(), MetalRate.get_last_dates(number=1)[0])
        self.assertEqual(MetalRate.get_last_date(), MetalRate.get_last_dates()[-1])

    def test_settings(self):
        self.assertEqual(Settings.instance(), Settings.instance())
        self.assertEqual(Settings.instance(), Settings.get_first())
        self.assertEqual(Settings.instance(), Settings.get_last())

        self.assertIsNone(Settings.get_last_date_of_metals_rate())
        self.assertIsNone(Settings.instance().last_date_of_metals_rate)

        expected = DT.date.today()
        Settings.set_last_date_of_metals_rate(expected)
        self.assertEqual(expected, Settings.get_last_date_of_metals_rate())
        self.assertEqual(expected, Settings.instance().last_date_of_metals_rate)

    def test_subscription(self):
        # Тестовый user_id
        user_id = random.randint(0, 999_999_999)

        self.assertTrue(Subscription.count() == 0)
        self.assertTrue(Subscription.get_active_unsent_subscriptions() == 0)
        self.assertIsNone(Subscription.get_by_user_id(user_id))
        self.assertFalse(Subscription.has_is_active(user_id))

        with self.subTest(msg='Unsubscribing new user'):
            result = Subscription.unsubscribe(user_id)
            self.assertEqual(SubscriptionResultEnum.ALREADY, result)

            self.assertTrue(Subscription.count() == 0)
            self.assertTrue(Subscription.get_active_unsent_subscriptions() == 0)
            self.assertIsNone(Subscription.get_by_user_id(user_id))
            self.assertFalse(Subscription.has_is_active(user_id))

        with self.subTest(msg='Repeat unsubscribing for new user'):
            result = Subscription.unsubscribe(user_id)
            self.assertEqual(SubscriptionResultEnum.ALREADY, result)

            self.assertTrue(Subscription.count() == 0)
            self.assertTrue(Subscription.get_active_unsent_subscriptions() == 0)
            self.assertIsNone(Subscription.get_by_user_id(user_id))
            self.assertFalse(Subscription.has_is_active(user_id))

        with self.subTest(msg='Subscribing new user'):
            result = Subscription.subscribe(user_id)
            self.assertEqual(SubscriptionResultEnum.SUBSCRIBE_OK, result)

            self.assertTrue(Subscription.count() == 1)
            self.assertTrue(Subscription.get_active_unsent_subscriptions() == 1)
            self.assertIsNotNone(Subscription.get_by_user_id(user_id))
            self.assertTrue(Subscription.has_is_active(user_id))

        with self.subTest(msg='Repeat subscribing of subscribed user'):
            result = Subscription.subscribe(user_id)
            self.assertEqual(SubscriptionResultEnum.ALREADY, result)

            self.assertTrue(Subscription.count() == 1)
            self.assertTrue(Subscription.get_active_unsent_subscriptions() == 1)
            self.assertIsNotNone(Subscription.get_by_user_id(user_id))
            self.assertTrue(Subscription.has_is_active(user_id))

        with self.subTest(msg='Unsubscribing of subscribed user'):
            result = Subscription.unsubscribe(user_id)
            self.assertEqual(SubscriptionResultEnum.UNSUBSCRIBE_OK, result)

            self.assertTrue(Subscription.count() == 1)
            self.assertTrue(Subscription.get_active_unsent_subscriptions() == 0)
            self.assertIsNotNone(Subscription.get_by_user_id(user_id))
            self.assertFalse(Subscription.has_is_active(user_id))

        with self.subTest(msg='Repeat unsubscribing of unsubscribed user'):
            result = Subscription.unsubscribe(user_id)
            self.assertEqual(SubscriptionResultEnum.ALREADY, result)

            self.assertTrue(Subscription.count() == 1)
            self.assertTrue(Subscription.get_active_unsent_subscriptions() == 0)
            self.assertIsNotNone(Subscription.get_by_user_id(user_id))
            self.assertFalse(Subscription.has_is_active(user_id))


class TestCasePlot(unittest.TestCase):
    def test_draw_plot(self):
        locator = mdates.YearLocator(3)

        days = []
        values = []
        for metal_rate in MetalRate.select():
            days.append(metal_rate.date)
            values.append(metal_rate.gold)

        title = "Стоимость грамма золота в рублях"

        with self.subTest(msg="BytesIO"):
            bytes_io = BytesIO()
            draw_plot(out=bytes_io, days=days, values=values, locator=locator, title=title)
            assert bytes_io.read()

        path = DIR / f'{uuid4()}.png'

        with self.subTest(msg="Path"):
            draw_plot(out=path, days=days, values=values, locator=locator, title=title)
            assert path.exists()
            assert path.read_bytes()
            path.unlink()

        with self.subTest(msg="str"):
            draw_plot(out=str(path), days=days, values=values, locator=locator, title=title)
            assert path.exists()
            assert path.read_bytes()
            path.unlink()

        with self.subTest(msg="Save with open"):
            with open(path, 'wb') as f:
                draw_plot(out=f, days=days, values=values, locator=locator, title=title)
            self.assertTrue(path.exists())
            self.assertTrue(path.read_bytes())
            path.unlink()

    def test_get_plot_for(self):
        for draw_func in [get_plot_for_gold, get_plot_for_silver, get_plot_for_platinum, get_plot_for_palladium]:
            for number in [7, 31, 180, -1]:
                with self.subTest(msg=draw_func.__name__, number=number):
                    photo = draw_func(number)
                    assert photo.read()


if __name__ == '__main__':
    unittest.main()
