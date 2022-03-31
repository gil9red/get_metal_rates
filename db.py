#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import enum
import time

from decimal import Decimal
from typing import Type, Optional, Iterable, Any

# pip install peewee
from peewee import (
    Model, TextField, ForeignKeyField, CharField, DecimalField, DateField, Field
)
from playhouse.sqliteq import SqliteQueueDatabase

from root_config import DB_FILE_NAME, ITEMS_PER_PAGE
from app_parser.config import START_DATE
from app_parser import parser


# SOURCE: https://github.com/gil9red/SimplePyScripts/blob/cd5bf42742b2de4706a82aecb00e20ca0f043f8e/shorten.py
def shorten(text: str, length=30) -> str:
    if not text:
        return text

    if len(text) > length:
        text = text[:length] + '...'

    return text


class EnumField(CharField):
    """
    This class enable an Enum like field for Peewee
    """

    def __init__(self, choices: Type[enum.Enum], *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self.choices: Type[enum.Enum] = choices
        self.max_length = 255

    def db_value(self, value: Any) -> Any:
        return value.value

    def python_value(self, value: Any) -> Any:
        type_value_enum = type(list(self.choices)[0].value)
        value_enum = type_value_enum(value)
        return self.choices(value_enum)


# This working with multithreading
# SOURCE: http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#sqliteq
db = SqliteQueueDatabase(
    DB_FILE_NAME,
    pragmas={
        'foreign_keys': 1,
        'journal_mode': 'wal',    # WAL-mode
        'cache_size': -1024 * 64  # 64MB page-cache
    },
    use_gevent=False,     # Use the standard library "threading" module.
    autostart=True,
    queue_max_size=64,    # Max. # of pending writes that can accumulate.
    results_timeout=5.0   # Max. time to wait for query to be executed.
)


class BaseModel(Model):
    """
    Базовая модель для классов-таблиц
    """

    class Meta:
        database = db

    def get_new(self) -> Type['BaseModel']:
        return type(self).get(self._pk_expr())

    @classmethod
    def get_first(cls) -> Type['BaseModel']:
        return cls.select().first()

    @classmethod
    def get_last(cls) -> Type['BaseModel']:
        return cls.select().order_by(cls.id.desc()).first()

    @classmethod
    def paginating(
            cls,
            page: int = 1,
            items_per_page: int = ITEMS_PER_PAGE,
            order_by: Field = None,
            filters: Iterable = None,
    ) -> list[Type['BaseModel']]:
        query = cls.select()

        if filters:
            query = query.filter(*filters)

        if order_by:
            query = query.order_by(order_by)

        query = query.paginate(page, items_per_page)
        return list(query)

    @classmethod
    def get_inherited_models(cls) -> list[Type['BaseModel']]:
        return sorted(cls.__subclasses__(), key=lambda x: x.__name__)

    @classmethod
    def count(cls) -> int:
        return cls.select().count()

    @classmethod
    def print_count_of_tables(cls):
        items = []
        for sub_cls in cls.get_inherited_models():
            name = sub_cls.__name__
            count = sub_cls.count()
            items.append(f'{name}: {count}')

        print(', '.join(items))

    def __str__(self):
        fields = []
        for k, field in self._meta.fields.items():
            v = getattr(self, k)

            if isinstance(field, (TextField, CharField)):
                if v:
                    if isinstance(v, enum.Enum):
                        v = v.value

                    v = repr(shorten(v))

            elif isinstance(field, ForeignKeyField):
                k = f'{k}_id'
                if v:
                    v = v.id

            fields.append(f'{k}={v}')

        return self.__class__.__name__ + '(' + ', '.join(fields) + ')'


class MetalRate(BaseModel):
    date = DateField(unique=True)
    gold = DecimalField(decimal_places=2, null=True)
    silver = DecimalField(decimal_places=2, null=True)
    platinum = DecimalField(decimal_places=2, null=True)
    palladium = DecimalField(decimal_places=2, null=True)

    @classmethod
    def get_by(cls, date: DT.date) -> Optional['MetalRate']:
        return cls.get_or_none(date=date)

    @classmethod
    def add(
            cls,
            date: DT.date,
            gold: Decimal = None,
            silver: Decimal = None,
            platinum: Decimal = None,
            palladium: Decimal = None,
    ) -> 'MetalRate':
        obj = cls.get_by(date)
        if not obj:
            obj = cls.create(
                date=date,
                gold=gold,
                silver=silver,
                platinum=platinum,
                palladium=palladium,
            )

        return obj

    @classmethod
    def add_from(cls, metal_rate: parser.MetalRate) -> 'MetalRate':
        return cls.add(
            date=metal_rate.date,
            gold=metal_rate.gold,
            silver=metal_rate.silver,
            platinum=metal_rate.platinum,
            palladium=metal_rate.palladium,
        )

    @classmethod
    def get_range_dates(cls) -> tuple[DT.date, DT.date]:
        return (
            cls.select(cls.date).limit(1).order_by(cls.date.asc()).first().date,
            cls.select(cls.date).limit(1).order_by(cls.date.desc()).first().date
        )

    @classmethod
    def get_prev_next_dates(cls, date: DT.date) -> tuple[DT.date, DT.date]:
        prev_val = cls.select(cls.date).where(cls.date < date).limit(1).order_by(cls.date.desc()).first()
        prev_date = prev_val.date if prev_val else None

        next_val = cls.select(cls.date).where(cls.date > date).limit(1).order_by(cls.date.asc()).first()
        next_date = next_val.date if next_val else None

        return prev_date, next_date

    @classmethod
    def get_last_date(cls) -> DT.date:
        return cls.get_last_dates(number=1)[0]

    @classmethod
    def get_last_dates(cls, number: int) -> list[DT.date]:
        query = cls.select(cls.date).limit(number).order_by(cls.date.desc())
        items = [rate.date for rate in query]
        if not items:
            items.append(START_DATE)
        return items

    @classmethod
    def get_last_rates(cls, number: int, ignore_null: bool = True) -> list['MetalRate']:
        dates = cls.get_last_dates(number)
        filters = [cls.date.in_(dates)]
        if ignore_null:
            # Все металлы должны быть заданы
            filters += [
                cls.gold.is_null(False),
                cls.silver.is_null(False),
                cls.platinum.is_null(False),
                cls.palladium.is_null(False),
            ]

        query = cls.select().where(*filters).order_by(cls.date.asc())
        return list(query)


db.connect()
db.create_tables(BaseModel.get_inherited_models())

# Задержка в 50мс, чтобы дать время на запуск SqliteQueueDatabase и создание таблиц
# Т.к. в SqliteQueueDatabase запросы на чтение выполняются сразу, а на запись попадают в очередь
time.sleep(0.050)

if __name__ == '__main__':
    BaseModel.print_count_of_tables()
    # MetalRate: 5516
    print()

    print('Last date:', MetalRate.get_last_date())
    # Last date: 2022-03-31

    start_date, end_date = MetalRate.get_range_dates()
    print(f'Range dates: {start_date} - {end_date}')
    # Range dates: 2000-01-06 - 2022-03-31

    print()

    print(f'Last metal rate (by date):\n    {MetalRate.get_by(end_date)}\n')
    # Last metal rate (by date):
    #     MetalRate(id=5516, date=2022-03-31, gold=5184.57, silver=66.92, platinum=2660.14, palladium=5839.34)

    print(f'Last metal rate (by method):\n    {MetalRate.get_last()}\n')
    # Last metal rate (by method):
    #     MetalRate(id=5516, date=2022-03-31, gold=5184.57, silver=66.92, platinum=2660.14, palladium=5839.34)

    print()

    date = DT.date.fromisoformat('2022-03-24')
    print(MetalRate.get_prev_next_dates(date))
    # (datetime.date(2022, 3, 23), datetime.date(2022, 3, 25))

    print(MetalRate.get_prev_next_dates(start_date))
    # (None, datetime.date(2000, 1, 10))

    print(MetalRate.get_prev_next_dates(end_date))
    # (datetime.date(2022, 3, 30), None)

    print()

    dates = MetalRate.get_last_dates(number=7)
    print('Last 7 dates:', [str(d) for d in dates])
    # Last 7 dates: ['2022-03-31', '2022-03-30', '2022-03-29', '2022-03-26', '2022-03-25', '2022-03-24', '2022-03-23']

    print()

    for metal_rate in MetalRate.get_last_rates(number=3):
        print(
            f'{metal_rate.date}:\n'
            f'    Gold: {metal_rate.gold}\n'
            f'    Silver: {metal_rate.silver}\n'
            f'    Platinum: {metal_rate.platinum}\n'
            f'    Palladium: {metal_rate.palladium}\n'
        )
    """
    2022-03-29:
        Gold: 5805.91
        Silver: 75.04
        Platinum: 2985.81
        Palladium: 6800.17
    
    2022-03-30:
        Gold: 5301.45
        Silver: 68.35
        Platinum: 2729.72
        Palladium: 6216.76
    
    2022-03-31:
        Gold: 5184.57
        Silver: 66.92
        Platinum: 2660.14
        Palladium: 5839.34
    """
