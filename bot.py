import os
import time
import logging
import gspread
from gspread.exceptions import CellNotFound
from test_system import run_code_on_tests

from aiogram import Bot, Dispatcher, executor, types
from telegram_token import API_TOKEN


class Table:
    def __init__(self, filename='domashka_credits.json'):
        gc = gspread.service_account(filename='domashka_credits.json')
        table = gc.open("Domashka_results")
        self.sheet =table.worksheets()[0]
        
    def find_user(self, username: str):
        try:
            return table.sheet.find(username, in_column=2).row
        except CellNotFound:
            return -1
        
    def put_mark(self, task:str, user_row: str, mark: int):
        try:
            col = self.sheet.find(task, in_row=1).col
#             row = self.sheet.find(user, in_column=1).row
            return self.sheet.update_cell(user_row, col, mark)['updatedCells'] == 1
        except Exception:
            pass
        return False
    
    def sort_by(self, col_name="сума балів", range='A2:ZZ50'):
        col = self.sheet.find(col_name).col
        self.sheet.sort((col, 'des'), range=range)

table = Table()
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer("Hi!\nI'm Python Domashka Bot!\nSend me your .py file. Results will apear here https://docs.google.com/spreadsheets/d/1RPwfEnb5kpVz6zh5AQamM-Dj3XNfAcTywkY8JU4Gmrc/edit?usp=sharing")

@dp.message_handler(commands=['table', 'results'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.answer("Таблицю результатів можна знайти тут https://docs.google.com/spreadsheets/d/1RPwfEnb5kpVz6zh5AQamM-Dj3XNfAcTywkY8JU4Gmrc/edit?usp=sharing")


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer("Пришли свій розв'язок в файлі з такою ж назвою як і задача та розширенням .py")

@dp.message_handler(content_types=types.ContentTypes.DOCUMENT)
async def document_recive(message: types.Message):
    username = message["from"]["username"]
    
    user_row = -1 if username is None else table.find_user(username) 
    
    if user_row == -1:
        await message.answer("вашого логіну немає в таблиці, напишіть викладачу аби він вас додав в список учнів")
        return
    taskname, extention = message.document.file_name.split(".")
    if extention != "py":
        await message.answer("файл повинен мати розширення .py")
        return
    if not os.path.exists("tests/" + taskname):
        await message.answer("немає такої задачі " + taskname)
        return
    await message.answer("отримав файл, перевіряю")
    await types.ChatActions.typing()
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    where2save = f"solutions/{username}/{taskname}/"
    os.makedirs(where2save, exist_ok=True)
    file_location = where2save + "_".join(map(str, list(time.localtime()))) + ".py"
    await bot.download_file(file.file_path, file_location)
    tests_pass, tests_num, error_message = run_code_on_tests(file_location, taskname)
    
    await message.answer(f"твій розв'язок пройшов {tests_pass} тестів з {tests_num}")
    if tests_pass != tests_num:
        await message.answer(f"твоя програма видала таку помилку\n{error_message}")
    
    #check for deadline

    mark = int(tests_pass/tests_num * 10)
    await message.answer(f"ти отримав {mark} балів")

    table.put_mark(taskname, user_row, mark)
    table.sort_by()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
