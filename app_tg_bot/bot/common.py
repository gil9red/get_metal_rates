#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'ipetrash'


import enum
import functools
import inspect
import json
import logging
from typing import Union, Optional

from telegram import (
    Update, ReplyMarkup, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
)
from telegram.error import NetworkError, BadRequest
from telegram.ext import CallbackContext
from telegram.utils.types import FileInput
from telegram.files.photosize import PhotoSize

from app_tg_bot.bot.regexp_patterns import PATTERN_INLINE_GET_AS_CHART
from app_tg_bot.bot.third_party.regexp import fill_string_pattern
from app_tg_bot.config import DIR_LOGS, MAX_MESSAGE_LENGTH, ERROR_TEXT
from root_common import get_logger, MetalEnum
from utils import draw_plot


# SOURCE: https://github.com/gil9red/telegram__random_bashim_bot/blob/e9d705a52223597c6965ef82f0b0d55fa11722c2/bot/parsers.py#L37
def caller_name() -> str:
    """Return the calling function's name."""
    return inspect.currentframe().f_back.f_code.co_name


def log_func(log: logging.Logger):
    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(update: Update, context: CallbackContext):
            if update:
                chat_id = user_id = first_name = last_name = username = language_code = None

                if update.effective_chat:
                    chat_id = update.effective_chat.id

                if update.effective_user:
                    user_id = update.effective_user.id
                    first_name = update.effective_user.first_name
                    last_name = update.effective_user.last_name
                    username = update.effective_user.username
                    language_code = update.effective_user.language_code

                try:
                    message = update.effective_message.text
                except:
                    message = ''

                try:
                    query_data = update.callback_query.data
                except:
                    query_data = ''

                msg = f'[chat_id={chat_id}, user_id={user_id}, ' \
                      f'first_name={first_name!r}, last_name={last_name!r}, ' \
                      f'username={username!r}, language_code={language_code}, ' \
                      f'message={message!r}, query_data={query_data!r}]'
                msg = func.__name__ + msg

                log.debug(msg)

            return func(update, context)

        return wrapper
    return actual_decorator


class SeverityEnum(enum.Enum):
    NONE = '{text}'
    INFO = 'ℹ️ {text}'
    ERROR = '⚠ {text}'

    def get_text(self, text: str) -> str:
        return self.value.format(text=text)


def reply_message(
        text: str,
        update: Update,
        context: CallbackContext,
        photo: Union[FileInput, PhotoSize] = None,
        severity: SeverityEnum = SeverityEnum.NONE,
        reply_markup: ReplyMarkup = None,
        quote: bool = True,
        **kwargs
):
    message = update.effective_message

    text = severity.get_text(text)

    if photo:
        # Для фото не будет разделения сообщения на куски
        mess = text[:MAX_MESSAGE_LENGTH]
        message.reply_photo(
            photo=photo,
            caption=mess,
            reply_markup=reply_markup,
            quote=quote,
            **kwargs
        )
    else:
        for n in range(0, len(text), MAX_MESSAGE_LENGTH):
            mess = text[n: n + MAX_MESSAGE_LENGTH]
            message.reply_text(
                mess,
                reply_markup=reply_markup,
                quote=quote,
                **kwargs
            )


def process_error(log: logging.Logger, update: Update, context: CallbackContext):
    log.error('Error: %s\nUpdate: %s', context.error, update, exc_info=context.error)
    if update:
        # Не отправляем ошибку пользователю при проблемах с сетью (типа, таймаут)
        if isinstance(context.error, NetworkError):
            return

        reply_message(ERROR_TEXT, update, context, severity=SeverityEnum.ERROR)


# SOURCE: https://github.com/gil9red/telegram__random_bashim_bot/blob/e9c98248f10c4a74f0e26dcf5a949bf2260f57d4/common.py#L177
def reply_text_or_edit_with_keyboard(
    message: Message,
    query: Optional[CallbackQuery],
    text: str,
    reply_markup: Union[InlineKeyboardMarkup, str],
    quote: bool = True,
    **kwargs,
):
    # Для запросов CallbackQuery нужно менять текущее сообщение
    if query:
        # Fix error: "telegram.error.BadRequest: Message is not modified"
        if text == query.message.text and is_equal_inline_keyboards(reply_markup, query.message.reply_markup):
            return

        try:
            message.edit_text(
                text,
                reply_markup=reply_markup,
                **kwargs,
            )
        except BadRequest as e:
            if 'Message is not modified' in str(e):
                return

            raise e

    else:
        message.reply_text(
            text,
            reply_markup=reply_markup,
            quote=quote,
            **kwargs,
        )


def reply_or_edit_plot_with_keyboard(
    metal: MetalEnum,
    number: int,
    update: Update,
    context: CallbackContext,
    quote: bool = True,
    **kwargs,
):
    message = update.effective_message
    query = update.callback_query
    if query:
        query.answer()

    photo = draw_plot.get_plot_for_metal(metal=metal, number=number)
    reply_markup = get_inline_keyboard_for_metal_switch_in_chart(
        current_metal=metal,
        number=number,
    )

    # Для запросов CallbackQuery нужно менять текущее сообщение
    if query:
        # Fix error: "telegram.error.BadRequest: Message is not modified"
        if is_equal_inline_keyboards(reply_markup, query.message.reply_markup):
            return

        try:
            message.edit_media(
                media=InputMediaPhoto(media=photo),
                reply_markup=reply_markup,
                **kwargs,
            )
        except BadRequest as e:
            if 'Message is not modified' in str(e):
                return

            raise e

    else:
        message.reply_photo(
            photo=photo,
            reply_markup=reply_markup,
            quote=quote,
            **kwargs,
        )


# SOURCE: https://github.com/gil9red/telegram__random_bashim_bot/blob/e9c98248f10c4a74f0e26dcf5a949bf2260f57d4/common.py#L147
def get_inline_keyboard_for_metal_switch_in_chart(
        current_metal: MetalEnum,
        number: Union[str, int],
) -> InlineKeyboardMarkup:
    pattern = PATTERN_INLINE_GET_AS_CHART

    buttons = []
    for metal in MetalEnum:
        metal_name = metal.name
        metal_title = metal.singular

        buttons.append(
            InlineKeyboardButton(
                text=f'· {metal_title} ·' if current_metal == metal else metal_title,
                callback_data=fill_string_pattern(pattern, number, metal_name)
            )
        )

    return InlineKeyboardMarkup.from_row(buttons)


def is_equal_inline_keyboards(
        keyboard_1: Union[InlineKeyboardMarkup, str],
        keyboard_2: InlineKeyboardMarkup
) -> bool:
    if isinstance(keyboard_1, InlineKeyboardMarkup):
        keyboard_1_inline_keyboard = keyboard_1.to_dict()['inline_keyboard']
    elif isinstance(keyboard_1, str):
        keyboard_1_inline_keyboard = json.loads(keyboard_1)['inline_keyboard']
    else:
        raise Exception(f'Unsupported format (keyboard_1={type(keyboard_1)})!')

    keyboard_2_inline_keyboard = keyboard_2.to_dict()['inline_keyboard']
    return keyboard_1_inline_keyboard == keyboard_2_inline_keyboard


log = get_logger(__file__, DIR_LOGS / 'log.txt')
