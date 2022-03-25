#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import unittest

from io import BytesIO
from pathlib import Path
from uuid import uuid4

# pip install matplotlib
import matplotlib.dates as mdates

from db import MetalRate

from utils.draw_plot import draw_plot


DIR = Path(__file__).resolve().parent


class TestCase(unittest.TestCase):
    def test_draw_plot(self):
        locator = mdates.YearLocator(3)

        days = []
        values = []
        for metal_rate in MetalRate.select():
            days.append(metal_rate.date)
            values.append(metal_rate.gold)

        title = f"Стоимость грамма золота в рублях"

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


if __name__ == '__main__':
    unittest.main()
