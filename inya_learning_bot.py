import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types
import datetime
from aiogram_calendar import SimpleCalendar, simple_cal_callback

API_TOKEN = '1767109592:AAHPy8GabHwBMirbfad6xWNdLknKSIbWUAw'
bot = Bot(token=API_TOKEN, timeout=100)
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
    await message.reply("Привет, Иня!")  # Моя любимая
    kb = types.reply_keyboard.ReplyKeyboardMarkup()
    sced = 'Расписание'
    kb.row(sced)
    await message.answer('Чего нада?!', reply_markup=kb)


@dp.message_handler(lambda message: message.text == 'Расписание')
async def schedule(message: types.Message):
    kb = types.reply_keyboard.ReplyKeyboardMarkup()
    kb.row('Сегодня', 'Завтра', 'Другой день')
    await message.answer('Напиши дату или выбери из предложенного!', reply_markup=kb)


@dp.message_handler(lambda message: message.text == 'Сегодня')
async def today(message: types.Message):
    text = get_schedule(message.date + datetime.timedelta(hours=5))
    if text:
        await message.answer(text)  # TODO: поправить часовой пояс
    else:
        await message.answer('Пар нет :3')


@dp.message_handler(lambda message: message.text == 'Завтра')
async def tomorrow(message: types.Message):
    text = get_schedule(message.date + datetime.timedelta(days=1, hours=5))
    if text:
        await message.answer(text)
    else:
        await message.answer('Пар нет :3')


@dp.message_handler(lambda message: message.text == 'Другой день')
async def other_day(message: types.Message):
    await message.answer('Выберите день, Госпожа!', reply_markup=await SimpleCalendar().start_calendar())


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    text = get_schedule(date + datetime.timedelta(days=1))
    if selected:
        if text:
            await callback_query.message.answer(text)
        else:
            await callback_query.message.answer('Пар нет :3')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, timeout=100)
