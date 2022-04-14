#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    Dispatcher, CallbackContext, MessageHandler, CommandHandler, Filters, CallbackQueryHandler
)

from app_tg_bot.bot.common import (
    reply_message, log_func, process_error, log, SeverityEnum,
    reply_text_or_edit_with_keyboard, reply_or_edit_plot_with_keyboard
)
from app_tg_bot.bot.regexp_patterns import (
    PATTERN_REPLY_GET_AS_TEXT, PATTERN_INLINE_GET_BY_DATE, PATTERN_REPLY_GET_LAST_7_AS_CHART,
    PATTERN_REPLY_GET_LAST_31_AS_CHART, PATTERN_REPLY_GET_ALL_AS_CHART, PATTERN_REPLY_SUBSCRIBE,
    PATTERN_REPLY_UNSUBSCRIBE, PATTERN_INLINE_GET_AS_CHART, fill_string_pattern
)

from db import Subscription, MetalRate
from root_common import get_date_str, MetalEnum, SubscriptionResultEnum, DEFAULT_METAL


def get_reply_keyboard(update: Update, context: CallbackContext) -> ReplyKeyboardMarkup:
    is_active = Subscription.has_is_active(update.effective_user.id)

    commands = [
        [fill_string_pattern(PATTERN_REPLY_GET_AS_TEXT)],
        [
            fill_string_pattern(PATTERN_REPLY_GET_LAST_7_AS_CHART),
            fill_string_pattern(PATTERN_REPLY_GET_LAST_31_AS_CHART)
        ],
        [fill_string_pattern(PATTERN_REPLY_GET_ALL_AS_CHART)],
        [fill_string_pattern(PATTERN_REPLY_UNSUBSCRIBE) if is_active else fill_string_pattern(PATTERN_REPLY_SUBSCRIBE)]
    ]
    return ReplyKeyboardMarkup(commands, resize_keyboard=True)


def get_inline_keyboard_for_date_pagination(for_date: DT.date) -> InlineKeyboardMarkup:
    prev_date, next_date = MetalRate.get_prev_next_dates(for_date)

    prev_date_str = f'❮ {get_date_str(prev_date)}' if prev_date else ''
    prev_date_callback_data = fill_string_pattern(PATTERN_INLINE_GET_BY_DATE, prev_date if prev_date else '')

    next_date_str = f'{get_date_str(next_date)} ❯' if next_date else ''
    next_date_callback_data = fill_string_pattern(PATTERN_INLINE_GET_BY_DATE, next_date if next_date else '')

    return InlineKeyboardMarkup.from_row([
        InlineKeyboardButton(text=prev_date_str, callback_data=prev_date_callback_data),
        InlineKeyboardButton(text=next_date_str, callback_data=next_date_callback_data),
    ])


@log_func(log)
def on_start(update: Update, context: CallbackContext):
    reply_message(
        f'Приветствую, {update.effective_user.name}! 🙂\n'
        'Данный бот способен отслеживать курсы драгоценных металлов и отправлять вам уведомление при появлении новых.\n'
        'С помощью меню вы можете подписаться/отписаться от рассылки, посмотреть курсы текстом или на графике',
        update=update,
        context=context,
        reply_markup=get_reply_keyboard(update, context),
    )


@log_func(log)
def on_get_as_text(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    try:
        for_date: DT.date = DT.date.fromisoformat(context.match.group(1))
        metal_rate: MetalRate = MetalRate.get_by(for_date)
    except:
        metal_rate: MetalRate = MetalRate.get_last()
        for_date: DT.date = metal_rate.date

    text = metal_rate.get_description()

    reply_text_or_edit_with_keyboard(
        message=update.effective_message,
        query=query,
        text=text,
        reply_markup=get_inline_keyboard_for_date_pagination(for_date),
    )


@log_func(log)
def on_get_last_7_as_chart(update: Update, context: CallbackContext):
    reply_or_edit_plot_with_keyboard(
        metal=DEFAULT_METAL,
        number=7,
        update=update,
        context=context,
    )


@log_func(log)
def on_get_last_31_as_chart(update: Update, context: CallbackContext):
    reply_or_edit_plot_with_keyboard(
        metal=DEFAULT_METAL,
        number=31,
        update=update,
        context=context,
    )


@log_func(log)
def on_get_all_as_chart(update: Update, context: CallbackContext):
    reply_or_edit_plot_with_keyboard(
        metal=DEFAULT_METAL,
        number=-1,
        update=update,
        context=context,
    )


@log_func(log)
def on_callback_get_as_chart(update: Update, context: CallbackContext):
    number_str, metal_name = context.match.groups()
    number = int(number_str)
    metal = MetalEnum[metal_name]

    reply_or_edit_plot_with_keyboard(
        metal=metal,
        number=number,
        update=update,
        context=context,
    )


@log_func(log)
def on_subscribe(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id

    result = Subscription.subscribe(user_id)
    match result:
        case SubscriptionResultEnum.ALREADY:
            text = 'Подписка уже оформлена!'
        case SubscriptionResultEnum.SUBSCRIBE_OK:
            text = 'Подписка успешно оформлена!'
        case _:
            raise Exception(f'Неожиданный результат {result} для метода "subscribe"!')

    reply_message(
        text=text,
        update=update,
        context=context,
        severity=SeverityEnum.INFO,
        reply_markup=get_reply_keyboard(update, context),
    )


@log_func(log)
def on_unsubscribe(update: Update, context: CallbackContext):
    message = update.effective_message
    user_id = message.from_user.id

    result = Subscription.unsubscribe(user_id)
    match result:
        case SubscriptionResultEnum.ALREADY:
            text = 'Подписка не оформлена!'
        case SubscriptionResultEnum.UNSUBSCRIBE_OK:
            text = 'Вы успешно отписались'
        case _:
            raise Exception(f'Неожиданный результат {result} для метода "unsubscribe"!')

    reply_message(
        text=text,
        update=update,
        context=context,
        severity=SeverityEnum.INFO,
        reply_markup=get_reply_keyboard(update, context),
    )


@log_func(log)
def on_request(update: Update, context: CallbackContext):
    reply_message(
        'Неизвестная команда',
        update=update,
        context=context,
        reply_markup=get_reply_keyboard(update, context),
        severity=SeverityEnum.ERROR,
        quote=True,
    )


def on_error(update: Update, context: CallbackContext):
    process_error(log, update, context)


def setup(dp: Dispatcher):
    dp.add_handler(CommandHandler('start', on_start))

    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_AS_TEXT), on_get_as_text))
    dp.add_handler(CallbackQueryHandler(on_get_as_text, pattern=PATTERN_INLINE_GET_BY_DATE))

    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_LAST_7_AS_CHART), on_get_last_7_as_chart))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_LAST_31_AS_CHART), on_get_last_31_as_chart))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_ALL_AS_CHART), on_get_all_as_chart))
    dp.add_handler(CallbackQueryHandler(on_callback_get_as_chart, pattern=PATTERN_INLINE_GET_AS_CHART))

    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_SUBSCRIBE), on_subscribe))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_UNSUBSCRIBE), on_unsubscribe))

    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)
