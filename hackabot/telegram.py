import collections
import logging
import threading
from pathlib import Path
from threading import Lock
from typing import Any, DefaultDict

import requests
import telebot
import granula
from text2speech.tinkoff_tts import generate

logger = logging.getLogger('telegram')


def get_full_name(user: telebot.types.User) -> str:
    name = user.first_name or ''
    if user.last_name:
        name += f' {user.last_name}'
    if user.username:
        name += f' @{user.username}'
    return name


def run_bot(token: str):
    locks: DefaultDict[Any, Lock] = collections.defaultdict(threading.Lock)
    bot = telebot.TeleBot(token)

    def _send(message: telebot.types.Message, response: str):
        bot.send_message(chat_id=message.chat.id, text=response, parse_mode='html')

    def _send_audio(message: telebot.types.Message):
        generate(message.text, message.chat.id)
        audio = open(f'synthesised{message.chat.id}.wav', 'rb')
        # tb.send_audio(chat_id, audio)
        bot.send_voice(chat_id=message.chat.id, voice=audio)

    @bot.message_handler(commands=['start'])
    def _start(message: telebot.types.Message):
        with locks[message.chat.id]:
            _send(message, response='Задавайте ваши вопросы')

    def _get_echo_response(text: str, user_id: str) -> str:
        return f'Добрый день, спутник! Не хотите немного кэшбэка?\n' \
 \
               f'Ваш идентификатор: {user_id}\nВаше сообщение: {text}'

    def _send_response(message: telebot.types.Message):
        chat_id = message.chat.id
        user_id = str(message.from_user.id) if message.from_user else '<unknown>'

        with locks[chat_id]:
            _send_audio(message)
            # try:
            #     response = _get_echo_response(message.text, user_id)
            # except Exception as e:
            #     logger.exception(e)
            #     response = 'Произошла ошибка'
            #
            # if response is None:
            #     response = 'Ответа нет'
            #
            # _send(message, response=response)

    @bot.message_handler()
    def send_response(message: telebot.types.Message):  # pylint:disable=unused-variable
        try:
            _send_response(message)
        except Exception as e:
            logger.exception(e)

    logger.info('Telegram bot started')
    bot.polling(none_stop=True)


def main():
    config_path = Path(__file__).parent / 'config.yaml'
    config = granula.Config.from_path(config_path)
    run_bot(config.telegram.key)


if __name__ == '__main__':
    while True:
        try:
            main()
        except requests.RequestException as e:
            logger.exception(e)
