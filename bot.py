import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from dotenv import load_dotenv

# --- 1. ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
# Подтягивает .env при локальном запуске; на хостинге подхватит системные переменные
load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW: str = os.getenv("ADMIN_ID", "0").strip()
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///bot.db").strip()

if not BOT_TOKEN:
    sys.exit("Ошибка: Переменная BOT_TOKEN не найдена в окружении!")

try:
    ADMIN_ID: int = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 0

# --- 2. ИНИЦИАЛИЗАЦИЯ И ХЭНДЛЕРЫ ---
dp = Dispatcher()


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! Бот запущен и готов к работе."
    )


@dp.message(Command("admin"))
async def handle_admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("У вас нет доступа к этой команде.")
        return
    await message.answer("Панель администратора активна.")


@dp.message()
async def handle_echo(message: types.Message):
    await message.answer(f"Вы написали: {message.text}")


# --- 3. ТОЧКА ВХОДА ---
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)

    # Пропуск накопившихся апдейтов при перезапуске бота
    await bot.delete_webhook(drop_pending_updates=True)

    logging.info("Бот успешно запущен.")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
  
