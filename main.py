import logging
import os
import telegram
import strapi

from dotenv import load_dotenv
from validate_email import validate_email
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


logger = logging.getLogger('telegram_shop')

user_states = {}


def start(bot, update):
    token = strapi_token()
    products = {
        product['attributes']['name']: product['id'] for product in strapi.get_products(token, base_url=STRAPI_BASE_URL)
    }
    keyboard = [
        [InlineKeyboardButton(product_name, callback_data=product_id)] for product_name, product_id in products.items()
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        update.message.reply_text(
            'Выбирайте, пожалуйста:',
            reply_markup=reply_markup
        )
    else:
        chat_id = update.callback_query.message.chat_id
        message_id = update.callback_query.message.message_id
        bot.send_message(
            chat_id=chat_id,
            reply_markup=reply_markup,
            text='Выбирайте, пожалуйста:'
        )
        bot.delete_message(chat_id=chat_id, message_id=message_id)

    return 'HANDLE_MENU'


def handle_menu(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    token = strapi_token()

    product_id = query.data
    product = strapi.get_products(token, product_id, base_url=STRAPI_BASE_URL)
    product_image_id = product['attributes']['image']['data'][0]['id']
    product_image_url = strapi.get_image_url(token, product_image_id, base_url=STRAPI_BASE_URL)

    caption = strapi.get_product_markdown_output(product)

    keyboard = [
        [InlineKeyboardButton(f'{quantity} шт.', callback_data=f'quantity/{product_id}/{quantity}') for quantity in range(1, 4)],
        [InlineKeyboardButton('🛒 Корзина', callback_data='cart')],
        [InlineKeyboardButton('◀️ Назад', callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_photo(
        chat_id=chat_id,
        photo=product_image_url,
        caption=caption,
        parse_mode=telegram.ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )

    bot.delete_message(chat_id=chat_id, message_id=message_id)

    return 'HANDLE_DESCRIPTION'


def handle_description(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    action = query.data.split('/')

    if action[0] == 'back':
        return start(bot, update)

    elif action[0] == 'cart':
        send_cart_keyboard(bot, chat_id)
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        return 'HANDLE_CART'

    elif action[0] == 'quantity':
        product_id, quantity = action[1], action[2]
        token = strapi_token()
        strapi.add_product_to_cart(token, chat_id, product_id, int(quantity), base_url=STRAPI_BASE_URL)
        update.callback_query.answer('Товар добавлен в корзину')
        return 'HANDLE_DESCRIPTION'


def handle_cart(bot, update):
    query = update.callback_query
    chat_id = query.message.chat_id
    message_id = query.message.message_id


    if query.data == 'menu':
        return start(bot, update)

    elif query.data == 'pay':
        bot.send_message(
            chat_id=chat_id,
            text='Пожалуйста, пришлите ваш email:'
        )
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        return 'HANDLE_WAITING_EMAIL'

    product_id = query.data
    token = strapi_token()
    strapi.remove_cart_item(token, chat_id, product_id, base_url=STRAPI_BASE_URL)

    send_cart_keyboard(bot, chat_id)
    bot.delete_message(chat_id=chat_id, message_id=message_id)
    return 'HANDLE_CART'


def handle_waiting_email(bot, update):
    chat_id = update.message.chat_id
    text = update.message.text

    keyboard = [
        [InlineKeyboardButton(f'◀️ В меню', callback_data='start')]
    ]

    if validate_email(text):
        bot.send_message(
            chat_id = chat_id,
            text=f'*Ваш заказ оформлен!*',
            parse_mode=telegram.ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        customer_name = update.message.chat.first_name
        token = strapi_token()
        strapi.create_customer(token, name=customer_name, email=text, base_url=STRAPI_BASE_URL)
        return 'START'

    bot.send_message(
        chat_id = chat_id,
        text=f'Кажется, вы неправильно ввели email, повторите пожалуйста:'
    )
    return 'HANDLE_WAITING_EMAIL'


def handle_users_reply(bot, update):
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

    
    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'HANDLE_WAITING_EMAIL': handle_waiting_email
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(bot, update)
        user_states[str(chat_id)] = next_state
    except Exception as error:
        logger.error(error)


def send_cart_keyboard(bot, chat_id):
    token = strapi_token()
    cart = strapi.get_cart(token, chat_id, base_url=STRAPI_BASE_URL)
    cart_items = strapi.get_cart_items(token, chat_id, base_url=STRAPI_BASE_URL)
    menu_button = [[InlineKeyboardButton('◀️ Меню', callback_data='menu')]]
    pay_button = [[InlineKeyboardButton('🤑 Оплатить', callback_data='pay')]]

    if not cart_items:
        bot.send_message(
            chat_id=chat_id,
            text='В корзине ничего нет :(',
            reply_markup=InlineKeyboardMarkup(menu_button),
        )

        return

    cart_items_formatted = strapi.get_formatted_cart_items(cart, cart_items)
    keyboard = [
        [InlineKeyboardButton(f'❌ Удалить {product["attributes"]["name"]}', callback_data=product['id'])] for product in cart_items
    ] + pay_button + menu_button

    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=chat_id,
        text=cart_items_formatted,
        reply_markup=reply_markup,
        parse_mode=telegram.ParseMode.MARKDOWN
    )





def get_strapi_token():
    """Get Strapi token"""
    return strapi.get_access_token(STRAPI_API_TOKEN)


if __name__ == '__main__':
    load_dotenv()

    STRAPI_API_TOKEN = os.getenv('STRAPI_API_TOKEN')
    STRAPI_BASE_URL = os.getenv('STRAPI_BASE_URL')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')

    # Create a global function for token retrieval
    strapi_token = get_strapi_token

    updater = Updater(TELEGRAM_TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', handle_users_reply))
    updater.start_polling()
    updater.idle()
