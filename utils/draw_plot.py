#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
from io import BytesIO

from decimal import Decimal
from pathlib import Path
from typing import BinaryIO, Union

# pip install matplotlib
import matplotlib.dates as mdates
from matplotlib.figure import Figure

from db import MetalRate
from root_config import DATE_FORMAT
from root_common import get_date_str, MetalEnum


def draw_plot(
        out: Union[str, Path, BinaryIO],
        days: list[DT.date],
        values: list[Decimal],
        locator: mdates.DateLocator = None,
        title: str = None,
        color: str = 'orange',
        date_format: str = DATE_FORMAT,
        axis_off: bool = False,
):
    if not locator:
        locator = mdates.AutoDateLocator()

    fig = Figure()
    ax = fig.subplots()
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    ax.xaxis.set_major_locator(locator)

    lines = ax.plot(days, values)[0]
    lines.set_color(color)

    if title:
        ax.set_xlabel(title)

    fig.autofmt_xdate()

    if axis_off:
        ax.set_xticks([])
        ax.set_yticks([])

    fig.savefig(out, format='png')

    # После записи в файловый объект нужно внутренний указатель переместить в начало, иначе read не будет работать
    if hasattr(out, 'seek'):  # Для BinaryIO и ему подобных
        out.seek(0)


def get_plot_for_metal(
    metal: MetalEnum,
    number: int = -1,
    title_format: str = "Стоимость грамма {metal_name} в рублях за {start_date} - {end_date}",
) -> BytesIO:
    days = []
    values = []
    for metal_rate in MetalRate.get_last_rates(number=number):
        days.append(metal_rate.date)
        values.append(getattr(metal_rate, metal.name_lower))

    title = title_format.format(
        metal_name=metal.plural,
        start_date=get_date_str(days[0]),
        end_date=get_date_str(days[-1])
    )

    bytes_io = BytesIO()
    draw_plot(
        out=bytes_io,
        days=days,
        values=values,
        title=title,
        color=metal.color,
    )
    return bytes_io


def get_plot_for_gold(number: int = -1) -> BytesIO:
    return get_plot_for_metal(MetalEnum.GOLD, number=number)


def get_plot_for_silver(number: int = -1) -> BytesIO:
    return get_plot_for_metal(MetalEnum.SILVER, number=number)


def get_plot_for_platinum(number: int = -1) -> BytesIO:
    return get_plot_for_metal(MetalEnum.PLATINUM, number=number)


def get_plot_for_palladium(number: int = -1) -> BytesIO:
    return get_plot_for_metal(MetalEnum.PALLADIUM, number=number)


if __name__ == '__main__':
    DIR = Path(__file__).resolve().parent

    for metal in MetalEnum:
        photo = get_plot_for_metal(metal)
        path = DIR / f'get_plot_for_{metal.name}.png'
        path.write_bytes(photo.read())

    days = []
    values = []
    for metal_rate in MetalRate.select():
        days.append(metal_rate.date)
        values.append(metal_rate.gold)

    title = f"Стоимость грамма золота в рублях за {get_date_str(days[0])} - {get_date_str(days[-1])}"

    path = DIR / 'draw_plot__plot_gold.png'
    draw_plot(
        out=path,
        days=days, values=values,
        title=title,
    )
