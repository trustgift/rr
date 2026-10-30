import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# --- 1. ЗАГРУЗКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ---
load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID_RAW: str = os.getenv("ADMIN_ID", "0").strip()

if not BOT_TOKEN:
    sys.exit("Ошибка: Переменная BOT_TOKEN не найдена в окружении!")

try:
    ADMIN_ID: int = int(ADMIN_ID_RAW)
except ValueError:
    ADMIN_ID = 0

if not ADMIN_ID:
    sys.exit("Ошибка: Укажите корректный ADMIN_ID в окружении!")

# --- 2. ИНИЦИАЛИЗАЦИЯ ---
dp = Dispatcher()

# Словарь для связи: message_id у админа -> user_id отправителя
# Позволяет отвечать даже если у юзера скрыт аккаунт или нет @username
MESSAGE_USER_MAP: dict[int, int] = {}


# --- 3. ХЭНДЛЕРЫ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ ---
@dp.message(CommandStart())
async def handle_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Вы администратор. Сообщения от пользователей со спамблоком будут приходить сюда.")
        return

    text = (
        f"Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Если у тебя спамблок или ты не можешь написать мне в личку — "
        "<b>просто отправь сюда свой вопрос или сообщение</b>.\n"
        "Я всё передам, и ответ придёт прямо в этот диалог."
    )
    await message.answer(text)


# Сообщения от пользователей (пересылаем админу)
@dp.message(F.from_user.id != ADMIN_ID)
async def forward_to_admin(message: types.Message, bot: Bot):
    user = message.from_user
    username_text = f"@{user.username}" if user.username else "нет username"

    # Информационная плашка перед сообщением
    header_text = (
        f"📩 <b>Новое сообщение</b>\n"
        f"От: <b>{user.full_name}</b> ({username_text})\n"
        f"ID: <code>{user.id}</code>\n"
        f"<i>Чтобы ответить, сделайте Reply (Ответить) на сообщение ниже ⬇️</i>"
    )

    await bot.send_message(chat_id=ADMIN_ID, text=header_text)

    # Копируем сообщение админу (сохраняет текст, кружки, фото, голосовые)
    forwarded = await message.copy_to(chat_id=ADMIN_ID)

    # Запоминаем ID сообщения, чтобы знать, кому отвечать при Reply
    MESSAGE_USER_MAP[forwarded.message_id] = user.id

    await message.answer("✅ Твоё сообщение отправлено! Ожидай ответа.")


# --- 4. ХЭНДЛЕРЫ ДЛЯ АДМИНА (ОТВЕТЫ) ---
@dp.message(F.from_user.id == ADMIN_ID)
async def reply_to_user(message: types.Message):
    # Проверяем, ответил ли админ через "Reply" (Ответить)
    if not message.reply_to_message:
        await message.answer(
            "⚠️ Чтобы отправить ответ пользователю, нажмите <b>Ответить (Reply)</b> на пересланное сообщение."
        )
        return

    replied_msg_id = message.reply_to_message.message_id
    target_user_id = MESSAGE_USER_MAP.get(replied_msg_id)

    # Если в памяти нет (например, бот перезагружался), проверяем forwarded_from
    if not target_user_id and message.reply_to_message.forward_from:
        target_user_id = message.reply_to_message.forward_from.id

    if not target_user_id:
        await message.answer(
            "❌ Не удалось определить получателя (возможно, бот перезапускался). "
            "Попроси пользователя отправить сообщение повторно."
        )
        return

    try:
        # Отправляем копию сообщения пользователю
        await message.copy_to(chat_id=target_user_id)
        await message.answer("🚀 Ответ успешно отправлен пользователю!")
    except Exception as e:
        await message.answer(f"❌ Ошибка при отправке (возможно, юзер заблокировал бота): {e}")


# --- 5. ТОЧКА ВХОДА ---
async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот обратной связи запущен.")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
