import logging
import os
import telegram
import strapi

from functools import partial
from dotenv import load_dotenv
from validate_email import validate_email
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


logger = logging.getLogger('telegram_shop')

user_states = {}


def start(bot, update, token, base_url):
    products = {
        product['attributes']['name']: product['id']
        for product in strapi.get_products(token, base_url=base_url)
    }

    keyboard = [
        [InlineKeyboardButton(name, callback_data=pid)]
        for name, pid in products.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text('Выбирайте, пожалуйста:', reply_markup=reply_markup)
    else:
        chat_id = update.callback_query.message.chat_id
        message_id = update.callback_query.message.message_id

        bot.send_message(chat_id=chat_id, text='Выбирайте, пожалуйста:', reply_markup=reply_markup)
        bot.delete_message(chat_id=chat_id, message_id=message_id)

    return 'HANDLE_MENU'


def handle_menu(bot, update, token, base_url):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    product_id = query.data
    product = strapi.get_products(token, product_id, base_url=base_url)

    image_id = product['attributes']['image']['data'][0]['id']
    image_url = strapi.get_image_url(token, image_id, base_url=base_url)

    caption = strapi.get_product_markdown_output(product)

    keyboard = [
        [InlineKeyboardButton(f'{q} шт.', callback_data=f'quantity/{product_id}/{q}') for q in range(1, 4)],
        [InlineKeyboardButton('🛒 Корзина', callback_data='cart')],
        [InlineKeyboardButton('◀️ Назад', callback_data='back')]
    ]

    bot.send_photo(
        chat_id=chat_id,
        photo=image_url,
        caption=caption,
        parse_mode=telegram.ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    bot.delete_message(chat_id=chat_id, message_id=message_id)

    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update, token, base_url):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    action = query.data.split('/')

    if action[0] == 'back':
        return start(bot, update, token, base_url)

    elif action[0] == 'cart':
        send_cart_keyboard(bot, chat_id, token, base_url)
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        return 'HANDLE_CART'

    elif action[0] == 'quantity':
        product_id, quantity = action[1], action[2]
        strapi.add_product_to_cart(token, chat_id, product_id, int(quantity), base_url=base_url)

        update.callback_query.answer('Товар добавлен в корзину')
        return 'HANDLE_DESCRIPTION'


def handle_cart(bot, update, token, base_url):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    if query.data == 'menu':
        return start(bot, update, token, base_url)

    elif query.data == 'pay':
        bot.send_message(chat_id=chat_id, text='Пожалуйста, пришлите ваш email:')
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        return 'HANDLE_WAITING_EMAIL'

    product_id = query.data
    strapi.remove_cart_item(token, chat_id, product_id, base_url=base_url)

    send_cart_keyboard(bot, chat_id, token, base_url)
    bot.delete_message(chat_id=chat_id, message_id=message_id)

    return 'HANDLE_CART'


def handle_waiting_email(bot, update, token, base_url):
    chat_id = update.message.chat_id
    text = update.message.text

    keyboard = [[InlineKeyboardButton('◀️ В меню', callback_data='start')]]

    if validate_email(text):
        bot.send_message(
            chat_id=chat_id,
            text='*Ваш заказ оформлен!*',
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        customer_name = update.message.chat.first_name
        strapi.create_customer(token, name=customer_name, email=text, base_url=base_url)

        return 'START'

    bot.send_message(chat_id=chat_id, text='Кажется, вы неправильно ввели email, повторите пожалуйста:')
    return 'HANDLE_WAITING_EMAIL'


def send_cart_keyboard(bot, chat_id, token, base_url):
    cart = strapi.get_cart(token, chat_id, base_url=base_url)
    cart_items = strapi.get_cart_items(token, chat_id, base_url=base_url)

    menu_button = [[InlineKeyboardButton('◀️ Меню', callback_data='menu')]]
    pay_button = [[InlineKeyboardButton('🤑 Оплатить', callback_data='pay')]]

    if not cart_items:
        bot.send_message(chat_id=chat_id, text='В корзине ничего нет :(', reply_markup=InlineKeyboardMarkup(menu_button))
        return

    text = strapi.get_formatted_cart_items(cart, cart_items)

    keyboard = [
        [InlineKeyboardButton(f'❌ Удалить {p["attributes"]["name"]}', callback_data=p['id'])]
        for p in cart_items
    ] + pay_button + menu_button

    bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=telegram.ParseMode.MARKDOWN
    )


def handle_users_reply(bot, update, token, base_url):
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = user_states.get(str(chat_id), 'START')

    states = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'HANDLE_WAITING_EMAIL': handle_waiting_email
    }

    try:
        next_state = states[user_state](bot, update, token, base_url)
        user_states[str(chat_id)] = next_state
    except Exception as error:
        logger.error(error)


def main():
    load_dotenv()

    strapi_api_token = os.environ['STRAPI_API_TOKEN']
    telegram_token = os.environ['TELEGRAM_TOKEN']
    base_url = os.getenv('STRAPI_BASE_URL')

    token = strapi.get_access_token(strapi_api_token)

    updater = Updater(telegram_token)
    dispatcher = updater.dispatcher

    handler = partial(handle_users_reply, token=token, base_url=base_url)

    dispatcher.add_handler(CallbackQueryHandler(handler))
    dispatcher.add_handler(MessageHandler(Filters.text, handler))
    dispatcher.add_handler(CommandHandler('start', handler))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
