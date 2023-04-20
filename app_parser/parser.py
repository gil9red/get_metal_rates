#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "ipetrash"


import datetime as DT
import decimal
from dataclasses import dataclass
from decimal import Decimal

import requests
from bs4 import BeautifulSoup

from app_parser.config import FILE_COOKIES, START_DATE
from root_common import get_date_str

decimal.getcontext().prec = 2

session = requests.session()

# NOTE: Зачем-то сайт с API добавил проверку на роботов, возможно, много запросов, а менять
#       работу сайта, добавляя API-key было сложно или много по времени
#       Example:
#       __ddgid=r6nn<...>4W; __ddg2=u5rq<...>wV9; __ddg1=gzBn<...>82mir; __ddgmark=W6X<...>owfI; __ddg5=ocM<...>tvM
if FILE_COOKIES.exists():
    try:
        cookies_text = FILE_COOKIES.read_text("utf-8")
        for x in cookies_text.split("; "):
            name, value = x.split("=", maxsplit=1)
            session.cookies.set(name, value)
    except:
        pass


@dataclass
class MetalRate:
    date: DT.date
    gold: Decimal = None
    silver: Decimal = None
    platinum: Decimal = None
    palladium: Decimal = None


def get_next_date(date: DT.date) -> DT.date:
    return (date + DT.timedelta(days=31)).replace(day=1)


def get_pair_dates(start_date: DT.date, end_date: DT.date = None) -> list[tuple[DT.date, DT.date]]:
    if not end_date:
        end_date = DT.date.today()

    items = []
    date_req1 = start_date

    while True:
        date_req1 = date_req1.replace(day=1)
        date_req2 = get_next_date(date_req1)
        items.append((date_req1, date_req2))

        if date_req2 > end_date:
            break

        date_req1 = date_req2

    return items


def get_metal_rates(date_req1: DT.date, date_req2: DT.date) -> list[MetalRate]:
    params = {
        "date_req1": get_date_str(date_req1),
        "date_req2": get_date_str(date_req2),
    }
    rs = session.get("http://www.cbr.ru/scripts/xml_metall.asp", params=params)
    rs.raise_for_status()

    root = BeautifulSoup(rs.content, "html.parser")
    date_by_metal_rate = dict()

    for tag in root.select("Record"):
        date = DT.datetime.strptime(tag["date"], "%d.%m.%Y").date()
        code = int(tag["code"])
        amount = decimal.Decimal(tag.sell.text.replace(",", "."))

        if date not in date_by_metal_rate:
            date_by_metal_rate[date] = MetalRate(date)

        metal_rate = date_by_metal_rate[date]

        match code:
            case 1: metal_rate.gold = amount
            case 2: metal_rate.silver = amount
            case 3: metal_rate.platinum = amount
            case 4: metal_rate.palladium = amount

    return list(date_by_metal_rate.values())


if __name__ == "__main__":
    pair_dates = get_pair_dates(START_DATE)
    date_req1_first, date_req2_first = pair_dates[0]
    date_req1_last, date_req2_last = pair_dates[-1]
    print(f"Total: {len(pair_dates)}")
    print(f"    {date_req1_first} - {date_req2_first}")
    print("    ...")
    print(f"    {date_req1_last} - {date_req2_last}")
    print()

    date_req1 = DT.date.today().replace(day=1)
    date_req2 = get_next_date(date_req1)

    metal_rates = get_metal_rates(date_req1, date_req2)
    print(f"Metal rates {date_req1} - {date_req2} ({len(metal_rates)}):")
    print(*metal_rates, sep="\n")
