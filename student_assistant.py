import requests
from bs4 import BeautifulSoup
from aiogram import Bot, Dispatcher, executor, types
import datetime
from aiogram_calendar import SimpleCalendar, simple_cal_callback
import sqlalchemy
from sqlalchemy.orm import mapper, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '1767109592:AAHPy8GabHwBMirbfad6xWNdLknKSIbWUAw'
bot = Bot(token=API_TOKEN, timeout=100)
dp = Dispatcher(bot, storage=MemoryStorage())


engine = sqlalchemy.create_engine('sqlite:///MyLove.db', echo=True)
base = declarative_base()


class Task(base):
    __tablename__ = 'Tasks'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    text = sqlalchemy.Column(sqlalchemy.String)

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return '{}|{}'.format(str(self.id), self.text)


Session = sessionmaker()
Session.configure(bind=engine)
session = Session()
base.metadata.create_all(engine)
session.commit()


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
@dp.message_handler(lambda message: message.text == 'В начало')
async def send_welcome(message: types.Message):
    if message.is_command():
        await message.answer("Привет!")
    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('Расписание')
    kb.row('Задачи')
    await message.answer('Введи запрос.', reply_markup=kb)


@dp.message_handler(lambda message: message.text == 'Расписание')
async def schedule(message: types.Message):
    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row('Сегодня', 'Завтра', 'Другой день')
    kb.row('В начало')
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
    await message.answer('Выберите день', reply_markup=await SimpleCalendar().start_calendar())


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: types.CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    text = get_schedule(date + datetime.timedelta(hours=5))
    if selected:
        if text:
            await callback_query.message.answer(text)
        else:
            await callback_query.message.answer('Пар нет :3')


class CreateTask(StatesGroup):
    waiting_for_description = State()


class DeleteTask(StatesGroup):
    waiting_for_confirmation = State()


@dp.message_handler(content_types=[types.ContentType.ANIMATION])
async def echo_document(message: types.Message):
    await message.reply_animation(message.animation.file_id)


@dp.message_handler(lambda message: message.text == 'Задачи')
async def tasks(message: types.Message):
    kb = types.reply_keyboard.ReplyKeyboardMarkup(resize_keyboard=True).add('Посмотреть', 'Создать', 'В начало')
    await message.answer('Выберите', reply_markup=kb)


@dp.message_handler(lambda message: message.text == 'Создать')
async def task_create(message: types.Message):
    await message.answer('Выкладывай')
    await CreateTask.waiting_for_description.set()


@dp.message_handler(state=CreateTask.waiting_for_description)
async def task_set_description(message: types.Message, state: FSMContext):
    session.add(Task(message.text))
    session.commit()
    await state.finish()
    await message.answer('Таск креатед')
    await send_welcome(message)


@dp.message_handler(lambda message: message.text == 'Посмотреть')
async def task_check(message: types.Message):
    query = session.query(Task).all()
    kb = types.InlineKeyboardMarkup()
    for task in query:
        kb.add(types.InlineKeyboardButton(text=task.text, callback_data='taskid=' + str(task.id)))
    await message.answer('Вот твои задачи:3', reply_markup=kb)


@dp.callback_query_handler(lambda call: 'taskid' in call.data)
async def task_delete_conformation(call: types.CallbackQuery):
    taskid = int(call.data.split('=')[-1])
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Да', callback_data='del_conform=' + str(taskid)))
    kb.add(types.InlineKeyboardButton(text='Нет', callback_data='del_cancel'))
    await call.message.answer('Ты хочешь удалить задачу?', reply_markup=kb)


@dp.callback_query_handler(lambda call: 'del_conform' in call.data)
async def task_delete(call: types.CallbackQuery):
    taskid = int(call.data.split('=')[-1])
    # session.delete(session.query(Task).filter(Task.id == taskid))
    session.query(Task).filter(Task.id == taskid).delete()
    session.commit()
    await call.message.answer('Задача удалена!')


@dp.callback_query_handler(lambda call: 'del_cancel' in call.data)
async def task_delete(call: types.CallbackQuery):
    await call.message.answer('Ну нет так нет...')
    await tasks(call.message)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, timeout=100)
