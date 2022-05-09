#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import datetime as DT

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ParseMode
from telegram.ext import (
    Dispatcher, CallbackContext, MessageHandler, CommandHandler, Filters, CallbackQueryHandler
)

from app_tg_bot.config import USER_NAME_ADMINS
from app_tg_bot.bot.common import (
    reply_message, log_func, process_error, log, SeverityEnum,
    reply_text_or_edit_with_keyboard, reply_or_edit_plot_with_keyboard, FORMAT_PREV, FORMAT_CURRENT, FORMAT_NEXT
)
from app_tg_bot.bot.regexp_patterns import (
    PATTERN_REPLY_ADMIN_STATS, COMMAND_ADMIN_STATS,
    PATTERN_REPLY_GET_AS_TEXT, PATTERN_INLINE_GET_BY_DATE,
    PATTERN_REPLY_GET_LAST_7_AS_CHART, PATTERN_REPLY_GET_LAST_31_AS_CHART,
    PATTERN_REPLY_GET_ALL_AS_CHART,
    PATTERN_REPLY_SUBSCRIBE, PATTERN_REPLY_UNSUBSCRIBE,
    PATTERN_INLINE_GET_AS_CHART,
    PATTERN_REPLY_SELECT_DATE, PATTERN_INLINE_SELECT_DATE,
    PATTERN_INLINE_GET_CHART_METAL_BY_YEAR,
    CALLBACK_IGNORE,
    fill_string_pattern
)
from app_tg_bot.bot.third_party.auto_in_progress_message import show_temp_message_decorator, ProgressValue
from app_tg_bot.bot.third_party import telegramcalendar

from db import Subscription, MetalRate
from root_common import get_date_str, MetalEnum, SubscriptionResultEnum, DEFAULT_METAL


FILTER_BY_ADMIN = Filters.user(username=USER_NAME_ADMINS)

TEXT_SHOW_TEMP_MESSAGE = SeverityEnum.INFO.get_text('Пожалуйста, подождите {value}')
PROGRESS_VALUE = ProgressValue.RECTS_SMALL


def get_reply_keyboard(update: Update, context: CallbackContext) -> ReplyKeyboardMarkup:
    is_active = Subscription.has_is_active(update.effective_user.id)

    commands = [
        [
            fill_string_pattern(PATTERN_REPLY_GET_AS_TEXT),
            fill_string_pattern(PATTERN_REPLY_SELECT_DATE),
        ],
        [
            fill_string_pattern(PATTERN_REPLY_GET_LAST_7_AS_CHART),
            fill_string_pattern(PATTERN_REPLY_GET_LAST_31_AS_CHART)
        ],
        [fill_string_pattern(PATTERN_REPLY_GET_ALL_AS_CHART)],
        [fill_string_pattern(PATTERN_REPLY_UNSUBSCRIBE) if is_active else fill_string_pattern(PATTERN_REPLY_SUBSCRIBE)]
    ]
    return ReplyKeyboardMarkup(commands, resize_keyboard=True)


def get_inline_keyboard_for_date_pagination(for_date: DT.date) -> InlineKeyboardMarkup:
    pattern = PATTERN_INLINE_GET_BY_DATE
    prev_date, next_date = MetalRate.get_prev_next_dates(for_date)

    buttons = []
    if prev_date:
        buttons.append(
            InlineKeyboardButton(
                text=FORMAT_PREV.format(get_date_str(prev_date)),
                callback_data=fill_string_pattern(pattern, prev_date),
            )
        )

    # Текущий выбор
    buttons.append(
        InlineKeyboardButton(
            text=FORMAT_CURRENT.format(get_date_str(for_date)),
            callback_data=fill_string_pattern(pattern, CALLBACK_IGNORE),
        )
    )

    if next_date:
        buttons.append(
            InlineKeyboardButton(
                text=FORMAT_NEXT.format(get_date_str(next_date)),
                callback_data=fill_string_pattern(pattern, next_date),
            )
        )

    return InlineKeyboardMarkup.from_row(buttons)


def get_inline_keyboard_for_year_pagination(current_metal: MetalEnum, year: int) -> InlineKeyboardMarkup:
    pattern = PATTERN_INLINE_GET_CHART_METAL_BY_YEAR
    prev_year, next_year = MetalRate.get_prev_next_years(year=year)

    # Список из 2 списков
    buttons: list[list[InlineKeyboardButton]] = [[], []]

    for metal in MetalEnum:
        metal_name = metal.name
        metal_title = metal.singular
        is_current = current_metal == metal

        buttons[0].append(
            InlineKeyboardButton(
                text=FORMAT_CURRENT.format(metal_title) if is_current else metal_title,
                callback_data=fill_string_pattern(
                    pattern,
                    CALLBACK_IGNORE if is_current else metal_name,
                    CALLBACK_IGNORE if is_current else year
                )
            )
        )

    if prev_year:
        buttons[1].append(
            InlineKeyboardButton(
                text=FORMAT_PREV.format(prev_year),
                callback_data=fill_string_pattern(pattern, current_metal.name, prev_year),
            )
        )

    # Текущий выбор
    buttons[1].append(
        InlineKeyboardButton(
            text=FORMAT_CURRENT.format(year),
            callback_data=fill_string_pattern(pattern, CALLBACK_IGNORE, CALLBACK_IGNORE),
        )
    )

    if next_year:
        buttons[1].append(
            InlineKeyboardButton(
                text=FORMAT_NEXT.format(next_year),
                callback_data=fill_string_pattern(pattern, current_metal.name, next_year)
            )
        )

    return InlineKeyboardMarkup(buttons)


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
def on_admin_stats(update: Update, context: CallbackContext):
    count = MetalRate.select().count()
    first_date = get_date_str(MetalRate.select().first().date)
    last_date = get_date_str(MetalRate.get_last().date)

    subscription_active_count = Subscription.select().where(Subscription.is_active == True).count()

    reply_message(
        f'<b>Статистика админа</b>\n\n'
        f'<b>Курсы валют</b>\n'
        f'Количество: <b><u>{count}</u></b>\n'
        f'Диапазон значений: <b><u>{first_date} - {last_date}</u></b>\n\n'
        f'<b>Подписки</b>\n'
        f'Количество активных: <b><u>{subscription_active_count}</u></b>',
        update=update, context=context,
        parse_mode=ParseMode.HTML,
        severity=SeverityEnum.INFO,
        reply_markup=get_reply_keyboard(update, context)
    )


@log_func(log)
def on_get_as_text(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    try:
        value: str = context.match.group(1)
        if value == CALLBACK_IGNORE:
            return

        for_date: DT.date = DT.date.fromisoformat(value)
        metal_rate: MetalRate = MetalRate.get_by(for_date)
    except:
        metal_rate: MetalRate = MetalRate.get_last()
        for_date: DT.date = metal_rate.date

    text = metal_rate.get_description(show_diff=True)

    reply_text_or_edit_with_keyboard(
        message=update.effective_message,
        query=query,
        text=text,
        reply_markup=get_inline_keyboard_for_date_pagination(for_date),
    )


@log_func(log)
def on_select_date(update: Update, context: CallbackContext):
    query = update.callback_query
    if not query:
        date = MetalRate.get_last_date()
        reply_message(
            "Пожалуйста, выберите дату:",
            update=update, context=context,
            reply_markup=telegramcalendar.create_calendar(
                year=date.year,
                month=date.month
            )
        )
        return

    query.answer()

    bot = context.bot

    selected, for_date = telegramcalendar.process_calendar_selection(bot, update)
    if selected:
        msg_not_found_for_date = ''

        metal_rate: MetalRate = MetalRate.get_by(for_date)
        if not metal_rate:
            msg_not_found_for_date = SeverityEnum.INFO.get_text(
                f'За {get_date_str(for_date)} нет данных, будет выбрана ближайшая дата'
            )
            prev_date, next_date = MetalRate.get_prev_next_dates(for_date)
            for_date = next_date if next_date else prev_date
            metal_rate: MetalRate = MetalRate.get_by(for_date)

        text = metal_rate.get_description(show_diff=True)
        if msg_not_found_for_date:
            text = msg_not_found_for_date + '\n\n' + text

        reply_text_or_edit_with_keyboard(
            message=update.effective_message,
            query=query,
            text=text,
            reply_markup=get_inline_keyboard_for_date_pagination(for_date),
        )


@log_func(log)
@show_temp_message_decorator(
    text=TEXT_SHOW_TEMP_MESSAGE,
    progress_value=PROGRESS_VALUE,
)
def on_get_last_7_as_chart(update: Update, context: CallbackContext):
    reply_or_edit_plot_with_keyboard(
        update=update,
        metal=DEFAULT_METAL,
        number=7,
    )


@log_func(log)
@show_temp_message_decorator(
    text=TEXT_SHOW_TEMP_MESSAGE,
    progress_value=PROGRESS_VALUE,
)
def on_get_last_31_as_chart(update: Update, context: CallbackContext):
    reply_or_edit_plot_with_keyboard(
        update=update,
        metal=DEFAULT_METAL,
        number=31,
    )


@log_func(log)
@show_temp_message_decorator(
    text=TEXT_SHOW_TEMP_MESSAGE,
    progress_value=PROGRESS_VALUE,
)
def on_get_all_as_chart(update: Update, context: CallbackContext):
    reply_or_edit_plot_with_keyboard(
        update=update,
        metal=DEFAULT_METAL,
        number=-1,
        reply_buttons_bottom=[
            InlineKeyboardButton(
                text='Посмотреть за определенный год',
                callback_data=fill_string_pattern(
                    PATTERN_INLINE_GET_CHART_METAL_BY_YEAR, DEFAULT_METAL.name, -1
                )
            ),
        ],
    )


@log_func(log)
@show_temp_message_decorator(
    text=TEXT_SHOW_TEMP_MESSAGE,
    progress_value=PROGRESS_VALUE,
)
def on_callback_get_as_chart(update: Update, context: CallbackContext):
    number_str, metal_name = context.match.groups()
    number = int(number_str)
    metal = MetalEnum[metal_name]

    reply_or_edit_plot_with_keyboard(
        update=update,
        metal=metal,
        number=number,
    )


@log_func(log)
@show_temp_message_decorator(
    text=TEXT_SHOW_TEMP_MESSAGE,
    progress_value=PROGRESS_VALUE,
)
def on_get_all_by_year(update: Update, context: CallbackContext):
    query = update.callback_query
    if query:
        query.answer()

    metal_name, year_str = context.match.groups()
    if metal_name == CALLBACK_IGNORE:
        return

    metal = MetalEnum[metal_name]
    year = int(year_str)
    if year == -1:
        year = MetalRate.get_last_date().year

    reply_or_edit_plot_with_keyboard(
        update=update,
        metal=metal,
        year=year,
        need_answer=False,
        reply_markup=get_inline_keyboard_for_year_pagination(metal, year),
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

    dp.add_handler(CommandHandler(COMMAND_ADMIN_STATS, on_admin_stats, FILTER_BY_ADMIN))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_ADMIN_STATS) & FILTER_BY_ADMIN, on_admin_stats))

    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_AS_TEXT), on_get_as_text))
    dp.add_handler(CallbackQueryHandler(on_get_as_text, pattern=PATTERN_INLINE_GET_BY_DATE))

    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_SELECT_DATE), on_select_date))
    dp.add_handler(CallbackQueryHandler(on_select_date, pattern=PATTERN_INLINE_SELECT_DATE))

    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_LAST_7_AS_CHART), on_get_last_7_as_chart))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_LAST_31_AS_CHART), on_get_last_31_as_chart))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_GET_ALL_AS_CHART), on_get_all_as_chart))
    dp.add_handler(CallbackQueryHandler(on_callback_get_as_chart, pattern=PATTERN_INLINE_GET_AS_CHART))

    dp.add_handler(CallbackQueryHandler(on_get_all_by_year, pattern=PATTERN_INLINE_GET_CHART_METAL_BY_YEAR))

    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_SUBSCRIBE), on_subscribe))
    dp.add_handler(MessageHandler(Filters.regex(PATTERN_REPLY_UNSUBSCRIBE), on_unsubscribe))

    dp.add_handler(MessageHandler(Filters.text, on_request))

    dp.add_error_handler(on_error)
