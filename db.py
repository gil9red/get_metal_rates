#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT
import enum
import time

from decimal import Decimal
from typing import Type, Optional, Iterable

# pip install peewee
from peewee import (
    Model, TextField, ForeignKeyField, CharField, DecimalField, DateField, Field, IntegerField, BooleanField,
    DateTimeField
)
from playhouse.sqliteq import SqliteQueueDatabase

from app_parser.config import START_DATE
from app_parser import parser
from root_config import DB_FILE_NAME
from root_common import get_date_str, SubscriptionResultEnum

ITEMS_PER_PAGE: int = 10


# SOURCE: https://github.com/gil9red/SimplePyScripts/blob/cd5bf42742b2de4706a82aecb00e20ca0f043f8e/shorten.py
def shorten(text: str, length=30) -> str:
    if not text:
        return text

    if len(text) > length:
        text = text[:length] + '...'

    return text


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

    def get_date_title(self) -> str:
        return get_date_str(self.date)

    @classmethod
    def get_by(cls, date: DT.date) -> Optional['MetalRate']:
        return cls.get_or_none(date=date)

    def get_description(self) -> str:
        return (
            f'{get_date_str(self.date)}:\n'
            f'    Золото: {self.gold}\n'
            f'    Серебро: {self.silver}\n'
            f'    Платина: {self.platinum}\n'
            f'    Палладий: {self.palladium}'
        )

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
    def get_last_dates(cls, number: int = -1) -> list[DT.date]:
        query = cls.select(cls.date).limit(number).order_by(cls.date.desc())
        items = [rate.date for rate in query]
        if not items:
            items.append(START_DATE)
        return items

    @classmethod
    def get_last_rates(cls, number: int = -1, ignore_null: bool = True) -> list['MetalRate']:
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


class Subscription(BaseModel):
    user_id = IntegerField(unique=True)
    is_active = BooleanField(default=True)
    was_sending = BooleanField(default=True)
    creation_datetime = DateTimeField(default=DT.datetime.now)
    modification_datetime = DateTimeField(default=DT.datetime.now)

    @classmethod
    def get_by_user_id(cls, user_id: int) -> Optional['Subscription']:
        return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def subscribe(cls, user_id: int) -> SubscriptionResultEnum:
        # Если подписка уже есть
        if cls.has_is_active(user_id):
            return SubscriptionResultEnum.ALREADY

        obj = cls.get_by_user_id(user_id)
        if obj:
            obj.set_active(True)
        else:
            # По-умолчанию, подписки создаются активными
            cls.create(user_id=user_id)

        return SubscriptionResultEnum.SUBSCRIBE_OK

    @classmethod
    def unsubscribe(cls, user_id: int) -> SubscriptionResultEnum:
        # Если подписка и так нет
        if not cls.has_is_active(user_id):
            return SubscriptionResultEnum.ALREADY

        obj = cls.get_by_user_id(user_id)
        if obj:
            obj.set_active(False)

        return SubscriptionResultEnum.UNSUBSCRIBE_OK

    @classmethod
    def get_active_unsent_subscriptions(cls) -> list['Subscription']:
        return cls.select().where(cls.was_sending == False, cls.is_active == True)

    @classmethod
    def has_is_active(cls, user_id: int) -> bool:
        return bool(cls.get_or_none(cls.user_id == user_id, cls.is_active == True))

    def set_active(self, active: bool):
        self.is_active = active
        if active:  # Чтобы сразу после подписки бот не отправил рассылку
            self.was_sending = True
        self.modification_datetime = DT.datetime.now()
        self.save()


class Settings(BaseModel):
    last_date_of_metals_rate = DateField(null=True)

    @classmethod
    def instance(cls) -> 'Settings':
        obj = cls.get_first()
        if not obj:
            obj = cls.create()

        return obj

    @classmethod
    def set_last_date_of_metals_rate(cls, value: DT.date):
        obj = cls.instance()
        obj.last_date_of_metals_rate = value
        obj.save()

    @classmethod
    def get_last_date_of_metals_rate(cls) -> Optional[DT.date]:
        return cls.instance().last_date_of_metals_rate


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
        print(metal_rate.get_description())
        print()
    """
    2022-03-29:
        Золото: 5805.91
        Серебро: 75.04
        Платина: 2985.81
        Палладий: 6800.17
    
    2022-03-30:
        Золото: 5301.45
        Серебро: 68.35
        Платина: 2729.72
        Палладий: 6216.76
    
    2022-03-31:
        Золото: 5184.57
        Серебро: 66.92
        Платина: 2660.14
        Палладий: 5839.34
    """

    obj = Settings.instance()
    print(obj)
    # Settings(id=1, last_date_of_metals_rate=None)
