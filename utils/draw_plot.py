#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT

from decimal import Decimal
from pathlib import Path
from typing import BinaryIO, Union

# pip install matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from db import MetalRate


DATE_FORMAT = '%d/%m/%Y'


def draw_plot(
        out: Union[str, Path, BinaryIO],
        days: list[DT.date],
        values: list[Decimal],
        locator: mdates.RRuleLocator,
        title: str = None,
        color: str = 'orange',
        date_format: str = DATE_FORMAT,
        show: bool = False
):
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    plt.gca().xaxis.set_major_locator(locator)

    lines = plt.plot(days, values)[0]
    lines.set_color(color)

    if title:
        plt.xlabel(title)

    plt.gcf().autofmt_xdate()

    plt.savefig(out)

    # После записи в файловый объект нужно внутренний указатель переместить в начало, иначе read не будет работать
    if hasattr(out, 'seek'):  # Для BinaryIO и ему подобных
        out.seek(0)

    if show:
        plt.show()


if __name__ == '__main__':
    locator = mdates.YearLocator(3)

    # TODO: поддержать и другие металлы
    # TODO: метод возвращения days, values по металлу + с заданной глубиной поиска:
    #         0, нет ограничения
    #         1 и более - количество записей назад
    days = []
    values = []
    for metal_rate in MetalRate.select():
        days.append(metal_rate.date)
        values.append(metal_rate.gold)

    title = f"Стоимость грамма золота в рублях за {days[0].strftime(DATE_FORMAT)} - {days[-1].strftime(DATE_FORMAT)}"

    DIR = Path(__file__).resolve().parent
    path = DIR / 'plot_gold.png'
    draw_plot(out=path, days=days, values=values, locator=locator, title=title, show=True)
