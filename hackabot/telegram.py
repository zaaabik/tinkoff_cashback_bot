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

import os, sys
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from speech_pack.tinkoff_stt import file_to_text
from speech_pack.tinkoff_tts import generate

from hackabot.link_stt import parse

logger = logging.getLogger('telegram')


def run_bot(token: str):
    locks: DefaultDict[Any, Lock] = collections.defaultdict(threading.Lock)
    bot = telebot.TeleBot(token)

    def _send(message: telebot.types.Message, response: str):
        bot.send_message(chat_id=message.chat.id, text=response, parse_mode='html')

    def _send_audio(chat_id, text):
        generate(text, chat_id)
        audio = open(f'synthesised{chat_id}.wav', 'rb')
        # tb.send_audio(chat_id, audio)
        bot.send_voice(chat_id=chat_id, voice=audio)

    def _send_photo(message: telebot.types.Message, photo):
        bot.send_photo(chat_id=message.chat.id, photo=photo)

    def training_parse(message: telebot.types.Message, state: int, req: str):
        req = ''.join(x for x in req if x.isalpha() or x == ' ')
        req = req.lower().split()

        chat_id = message.chat.id

        if state == 0:
            is_correct = False
            for r in req:
                if r.startswith('кофе'):
                    # MAKE VOICE
                    _send_audio(chat_id, 'Есть классный Мираторг в ТЦ Амальтея в 7 минут пешком от тебя.\
                    Получи кешбек 10% и разблокируй новую локацию! Адрес кину в сообщении. Скажи готово, когда оплатишь и насладишься кофе')
                    # END VOICE
                    _send(message, response='Мираторг, Большой бульвар, 40')
                    _send_audio(chat_id, 'Скажи готово, как насладишься своим кофе')

                    with open('users.json', 'r') as f:
                        tmp = json.load(f)
                    tmp[str(chat_id)]['current_state'] = 1
                    with open('users.json', 'w') as f:
                        json.dump(tmp, f)
                    is_correct = True
                    break

            if not is_correct:
                _send_audio(chat_id,
                            'Давай сначала ознакомимся с основными возможностями, а потом сможем свободно поболтать '
                            'или поискать что-то еще. Спроси меня, пожалуйста, о кофе.')
        elif state == 1:
            is_correct = False
            for r in req:
                if r.startswith('готово'):
                    _send_audio(chat_id, 'Отлично! Ты открыл новую локацию, вот она на карте:')
                    f = open(os.path.join('..', 'images', "after.jpg"), 'rb')
                    _send_photo(message, f)
                    _send_audio(chat_id, 'Теперь спроси меня о своей позиции в рейтинге.')
                    try:
                        with open('users.json', 'r') as f:
                            tmp = json.load(f)
                    except:
                        tmp = {}
                    tmp[str(chat_id)]['current_state'] = 2
                    with open('users.json', 'w') as f:
                        json.dump(tmp, f)

                    is_correct = True
                    break
            if not is_correct:
                _send_audio(chat_id, 'Всё еще жду, когда ты допьешь кофе.')
        elif state == 2:
            is_correct = False
            for r in req:
                if r.startswith('рейт'):
                    _send(message,
                          'Ваш рейтинг - 1583 по Москве. Вы в топ-20%! Войдите в топ-10% и удвойте свой кешбек!')
                    _send_audio(chat_id,
                                'На этом введение закончено. Если я буду тебе нужен, обращайся, если забудешь, что я умею, спроси помощи.')
                    try:
                        with open('users.json', 'r') as f:
                            tmp = json.load(f)
                    except:
                        tmp = {}
                    tmp[str(message.chat.id)]['current_state'] = 3
                    with open('users.json', 'w') as f:
                        json.dump(tmp, f)
                    is_correct = True
                    break
            if not is_correct:
                _send_audio(chat_id, 'Тебе не интересно узнать на сколько ты продвинулся? Спроси меня про рейтинг')

    def get_full_name(user: telebot.types.User) -> str:
        name = user.first_name or ''
        if user.last_name:
            name += f' {user.last_name}'
        if user.username:
            name += f' @{user.username}'
        return name

    @bot.message_handler(commands=['start'])
    def _start(message: telebot.types.Message):
        chat_id = message.chat.id
        with locks[message.chat.id]:
            _send_audio(chat_id,
                        'Открывай новые локации, лови кешбек, поднимайся в рейтинге. Трать с умом и получай еще больше!')
            # time.sleep(1)
            _send_audio(chat_id,
                        'Сейчас расскажу правила и проведу через короткое обучение. \nВ Игру, наш финансово грамотный друг, в игру!')
            # time.sleep(1)
            _send_audio(chat_id,
                        'Суть проста: набираешь как можно больше кэшбэка за время акции (я помогу тебе в этом!) - получаешь повышенный кешбэк НА ВСЕ в течение 3х месяцев. И это еще не все! Получай скидки от партнеров за ачивки в игре.')
            # time.sleep(1)
            _send_audio(chat_id,
                        'Что за ачивки? Получай их за открытие новых локаций! \nПока открыто очень мало, смотри:')
            f = open(os.path.join('..', 'images', "before.jpg"), 'rb')
            _send_photo(message, f)  # отправить картонку до
            _send_audio(chat_id,
                        'A теперь спроси меня, где кофейня с лучшим кешбэком рядом с тобой? Можно и нужно голосом!')
        try:
            with open('users.json', 'r') as f:
                tmp = json.load(f)
        except:
            tmp = {}
        tmp[str(message.chat.id)] = {'current_state': 0}
        with open('users.json', 'w') as f:
            json.dump(tmp, f)

    @bot.message_handler(content_types=['location'])
    def handle_location(message):
        sq_size = 100 / 10000
        latitude, longitude = message.location.latitude, message.location.longitude
        bottom_right = latitude - sq_size / 2, longitude + sq_size / 2
        top_left = latitude + sq_size / 2, longitude - sq_size / 2

        with open('users.json', 'r') as f:
            tmp = json.load(f)

        places_query = tmp[str(message.chat.id)]['request']
        headers = {'Content-Type': 'application/json'}
        params = {
            "geo_query": {
                "bottom_right": {
                    "lat": bottom_right[0],
                    "lon": bottom_right[1]
                },
                "top_left": {
                    "lat": top_left[0],
                    "lon": top_left[1]
                }
            },
            "query": places_query,
            "count": 3
        }

        r = requests.post('https://api-common-gw.tinkoff.ru/search/api/v1/search_merchants',
                          headers=headers, json=params)

        search_merchs = r.json()['search_result']['hits']
        if len(search_merchs) == 0:
            _send_audio(message.chat.id, "К сожаления рядом с вами ничего не нашлось")
            return
        # global geo, names, adresses
        # geo = search_merchs['geo']
        names = [merch['merchant_display_name'] or '' for merch in search_merchs]
        adresses = [merch['geo'][0]['address'] or '' for merch in search_merchs]
        name_address = [x + '\n' + y for x, y in zip(names, adresses)]

        _send_audio(message.chat.id, 'Нашел лучшие места. Сейчас кину в сообщении')  # replace witj speech

        for search_merch, name in zip(search_merchs, name_address):
            geo = search_merch['geo'][0]
            _send(message, response=name)
            bot.send_location(message.chat.id, geo['lat'], geo['lon'])

    def _send_response(message: telebot.types.Message):
        chat_id = message.chat.id
        user_id = str(message.from_user.id) if message.from_user else '<unknown>'

        with locks[chat_id]:
            try:
                _send_audio(chat_id, message.text)
            except Exception as e:
                _send(message, response='Не смог распознать')

    @bot.message_handler(func=lambda message: True,
                         content_types=['voice'])
    def handel_voice(message: telebot.types.Message):
        chat_id = message.chat.id
        with locks[chat_id]:
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

                with open('users.json', 'r') as f:
                    tmp = json.load(f)
                    state = tmp[str(message.chat.id)]['current_state']
                    if state == 0 or state == 1 or state == 2:
                        training_parse(message, tmp[str(message.chat.id)]['current_state'], response)
                    else:
                        msg, type = parse(req=response, user_id=message.chat.id)
                        if type == 'audio':
                            _send_audio(chat_id, msg)
                        elif type == 'image':
                            with open(msg, 'rb') as img:
                                _send_photo(message, img.read())
                        elif type == 'text':
                            _send(message, msg)

            except Exception as e:
                print(e)
                bot.send_message(message.chat.id, 'Не удалось распознать текст (((. У меня ляпки')

    @bot.message_handler()
    def send_response(message: telebot.types.Message):  # pylint:disable=unused-variable
        chat_id = message.chat.id
        try:
            response = message.text

            with open('users.json', 'r') as f:
                tmp = json.load(f)
                state = tmp[str(message.chat.id)]['current_state']
                if state == 0 or state == 1 or state == 2:
                    training_parse(message, tmp[str(message.chat.id)]['current_state'], response)
                else:
                    msg, type = parse(req=response, user_id=message.chat.id)
                    if type == 'audio':
                        _send_audio(chat_id, msg)
                    elif type == 'image':
                        with open(msg, 'rb') as img:
                            _send_photo(message, img.read())
                    elif type == 'text':
                        _send(message, msg)

        except Exception as e:
            print(e)
            bot.send_message(message.chat.id, 'Не удалось распознать текст (((. У меня ляпки')

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
