import telebot
import requests
from bs4 import BeautifulSoup
import random
import os

bot = telebot.TeleBot('1698850662:AAH5uh9R1tGiyC5i43yp1P-qeHmD0YJB3Qw')

url = 'https://safebooru.org/index.php?page=post&s=list&tags='


@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, "Hello! I can deliver u some pics by request. What do u like?")


@bot.message_handler(commands=['tag'])
def tag_command(message):
    bot.send_message(message.chat.id, "Hello! I can deliver u some pics by request. What do u like?")
    keyboard = telebot.types.InlineKeyboardMarkup()
    key_safe = telebot.types.InlineKeyboardButton(text='Safe', callback_data=1)
    keyboard.add(key_safe)
    key_questionable = telebot.types.InlineKeyboardButton(text='Somewhat dangerous', callback_data=2)
    keyboard.add(key_questionable)
    bot.send_message(message.from_user.id, text='Choose', reply_markup=keyboard)


@bot.message_handler(content_types='text')
def text_response(message):
    if message == 'Safe':
        pass
    elif message == 'Somewhat dangerous':
        pass


@bot.callback_query_handler(lambda call: 1)
def send_not_nudes(message):
    path = "B:\\Pictures\\KAWAII\\"
    file = random.choice(os.listdir(path))
    bot.send_photo(message.from_user.id, open(path+file, 'rb'))


@bot.callback_query_handler(lambda call: 2)
def send_nudes(message):
    path = "B:\\Pictures\\KAWAII+\\"
    file = random.choice(os.listdir(path))
    bot.send_photo(message.from_user.id, open(path+file, 'rb'))

bot.polling()
