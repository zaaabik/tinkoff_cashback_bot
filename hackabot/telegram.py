import collections
import logging
import os
import threading
from pathlib import Path
from threading import Lock
from typing import Any, DefaultDict

import requests
import telebot
import granula
import time
import json

from speech_pack.tinkoff_stt import file_to_text
from speech_pack.tinkoff_tts import generate

from .link_stt import parse

logger = logging.getLogger('telegram')


def training_parse(message: telebot.types.Message, state: int, req: str):
    req = ''.join(x for x in req if x.isalpha() or x == ' ')
    req = req.lower().split()

    if state == 0:
        for r in req:
            if r.startswith('кофе'):
                #MAKE VOICE
                _send(message, response='Есть классный Мираторг в ТЦ Амальтея в 7 минут пешком от тебя.\
                     Получи кешбек 10% и разблокируй новую локацию! Адрес кину в сообщении. Скажи готово, когда оплатишь и насладишься кофе')
                #END VOICE
                _send(message, response='Мираторг, Большой бульвар, 40')
    elif state == 1:
        for r in req:
            if r.startswith('рейт'):
                _send(message, response='Ваш рейтинг - N по Москве. Вы в топ-20%! Войдите в топ-10% и удвойте свой кешбек!')


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
            _send(message, response='Открывай новые локации, \
             лови кешбек, поднимайся в рейтинге. Трать с умом и получай еще больше!')
            time.sleep(1)
            _send(message, response='Сейчас расскажу правила и проведу через короткое обучение. \
                 В Игру, наш финансово грамотный друг, в игру!')
            time.sleep(1)
            _send(message, response='Суть проста: набираешь как можно больше кэшбэка \
                 за время акции (я помогу тебе в этом!) - получаешь повышенный кешбэк НА ВСЕ в течение 3х месяцев. И это еще не все! Получай скидки от партнеров за ачивки в игре.')
            time.sleep(1)
            _send(message, response='Что за ачивки? Получай их за открытие новых локаций! \
                Пока открыто очень мало, смотри:')
            #отправить картонку до
            _send(message, response='A теперь спроси меня, где кофейня с лучшим кешбэком рядом с тобой? Можно и нужно голосом!')
        try:
            with open('users.json', 'r') as f:
                tmp = json.load(f)
        except:
            tmp = {}
        tmp[message.chat.id] = {'current_state': 0}
        with open('users.json', 'w') as f:
            json.dump(tmp, f)
        

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        sq_size = 25 / 10000
        latitude, longitude = message.location.latitude, message.location.longitude
        coor0 = (latitude + sq_size / 2, longitude + sq_size / 2)
        coor1 = (latitude - sq_size / 2, longitude - sq_size / 2)

        headers = {'Content-Type': 'application/json'}
        params = {
        "geo_query": {
            "bottom_right": {
                "lat": 55.73741399385868,
                "lon": 37.56961595778349
            },
            "top_left": {
                "lat": 55.742244061297384,
                "lon": 37.56546389822844
            }
        },
        "query": places_query,
        "count": 3
        }

        r = requests.post('https://api-common-gw.tinkoff.ru/search/api/v1/search_merchants',
        headers = headers, json = params)

        search_merchs = r.json()['search_result']['hits']
        #global geo, names, adresses
        #geo = search_merchs['geo']
        names = [merch['merchant_display_name'] for merch in search_merchs]
        adresses = [merch['geo'][0]['address'] for merch in search_merchs]
        name_address = [x + ' ' + y for x,y in zip(names, adresses)]

        _send(message, response='Нашел лучшие места. Сейчас кину в сообщении') #replace witj speech
        _send(message, response=name_address[0])
        #add location
        _send(message, response=name_address[1])
        #add location
        _send(message, response=name_address[2])
        #add location

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

    @bot.message_handler(func=lambda message: True,
                         content_types=['voice'])
    def handel_voice(message: telebot.types.Message):
        try:
            file = bot.get_file(message.voice.file_id)
            voice_message = bot.download_file(file.file_path)
            voice_file_name = f'voice{message.chat.id}.ogg'
            with open(
                    os.path.join(
                        '..',
                        'voices',
                        voice_file_name
                    )
                    , 'wb+') as f:
                f.write(voice_message)

                response = file_to_text(voice_file_name)
                #bot.send_message(message.chat.id, response)
                with open('users.json', 'r') as f:
                    tmp = json.load(f)
                    if tmp[message.chat.id]['current_state'] == 0 or tmp[message.chat.id]['current_state'] == 1:
                        training_parse(message, tmp[message.chat.id]['current_state'], response)
                    else:
                        parse(user_id=message.chat.id)

        except Exception as e:
            bot.send_message(message.chat.id, 'Не удалось распознать текст (((. У меня ляпки')

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
