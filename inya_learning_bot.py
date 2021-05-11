import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types
import datetime
import pytz

API_TOKEN = '1767109592:AAHPy8GabHwBMirbfad6xWNdLknKSIbWUAw'
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def next_day(day):
    days = {'Понедельник': 0, 'Вторник': 1, 'Среда': 2,
            'Четверг': 3, 'Пятница': 4, 'Суббота': 5, 'Воскресенье': 6}
    nums = {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг',
            4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'}
    n = (days[day] + 1) % 6
    return nums[n]


def get_day_of_week(date):
    wnums = {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг',
             4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'}
    nums = date.isocalendar()[1]
    n = 1
    if (nums % 2) == 0:
        n = 2  # Чётная неделя или нет

    if (nums % 2) != 0:
        n = 1
    day = wnums[date.weekday()]
    return day, n - 1


def get_schedule(date):
    url = 'https://bsu.ru/rasp/?g='
    group = '17300'
    # group = input()
    day, n = get_day_of_week(date)
    page = requests.get(url + group).text
    soup = BeautifulSoup(page, features="html.parser")
    soup = soup.find_all(attrs={'class': 'week'})
    soup = soup[n]
    soup = soup.find(attrs={'class': 'rasp_week'})
    soup = soup.find_all('tr')
    nextday = next_day(day)
    rasp = []
    found = False
    for tr in soup:
        if found:
            try:
                if tr.find(attrs={'class': 'rasp_day'}).text == nextday:
                    break
            except AttributeError:
                pass
            try:
                subj = [tr.find(attrs={'class': 'rasp_time'}).text, tr.find(attrs={'class': 'rasp_subj'}).find('span').text,
                    tr.find(attrs={'class': 'rasp_subj_type'}).text, tr.find(attrs={'class': 'rasp_aud'}).text]
                rasp.append(' '.join(subj))
            except AttributeError:
                pass
        try:
            if tr.find(attrs={'class': 'rasp_day'}).text == day:
                found = True
        except AttributeError:
            pass
    return '\n'.join(rasp)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет, Иня!")
    kb = types.reply_keyboard.ReplyKeyboardMarkup()
    sced = 'Расписание'
    kb.add(sced)
    await message.answer('Чего нада?!', reply_markup=kb)


@dp.message_handler(lambda message: message.text == 'Расписание')
async def schedule(message: types.Message):
    kb = types.reply_keyboard.ReplyKeyboardMarkup()
    kb.add('Сегодня', 'Завтра')
    await message.answer('Напиши дату или выбери из предложенного!', reply_markup=kb)


@dp.message_handler(lambda message: message.text == 'Сегодня')
async def schedule(message: types.Message):
    await message.answer(get_schedule(message.date))


@dp.message_handler(lambda message: message.text == 'Завтра')
async def schedule(message: types.Message):
    await message.answer(get_schedule(message.date + datetime.timedelta(days=1)))


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
