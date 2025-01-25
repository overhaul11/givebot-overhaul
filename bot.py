import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальные переменные для хранения участников и настроек розыгрыша
participants = []
raffle_settings = {
    "winners_count": 1,
    "is_active": False,
    "description": ""
}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) начал взаимодействие с ботом.")
    await update.message.reply_text(
        "🎉 Добро пожаловать в бота для розыгрышей! 🎉\n"
        "Используй команду /setraffle, чтобы настроить розыгрыш."
    )

# Команда /setraffle
async def set_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) начал настройку розыгрыша.")

    # Запрашиваем описание розыгрыша
    await update.message.reply_text(
        "Введите описание розыгрыша:"
    )
    context.user_data["step"] = "set_description"

# Обработка текстовых сообщений для настройки розыгрыша
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    text = update.message.text

    if context.user_data.get("step") == "set_description":
        raffle_settings["description"] = text
        await update.message.reply_text(
            "Введите количество победителей:"
        )
        context.user_data["step"] = "set_winners_count"
    elif context.user_data.get("step") == "set_winners_count":
        try:
            winners_count = int(text)
            if winners_count <= 0:
                await update.message.reply_text("Количество победителей должно быть больше 0.")
                return
            raffle_settings["winners_count"] = winners_count
            await update.message.reply_text(
                f"Розыгрыш настроен!\n"
                f"Описание: {raffle_settings['description']}\n"
                f"Количество победителей: {raffle_settings['winners_count']}\n"
                "Используйте команду /publishraffle, чтобы опубликовать розыгрыш."
            )
            context.user_data["step"] = None
        except ValueError:
            await update.message.reply_text("Пожалуйста, введите число.")

# Команда /publishraffle
async def publish_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not raffle_settings["description"]:
        await update.message.reply_text("Сначала настройте розыгрыш с помощью команды /setraffle.")
        return

    raffle_settings["is_active"] = True
    user = update.message.from_user
    logger.info(f"Пользователь {user.first_name} ({user.id}) опубликовал розыгрыш.")

    # Создаем клавиатуру с кнопкой для участия через мини-приложение
    keyboard = [
        [InlineKeyboardButton("Участвовать через мини-приложение 🎁", web_app=WebAppInfo(url="https://github.com/overhaul11/Overhaul-Giveaway"))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем сообщение с кнопкой
    await update.message.reply_text(
        f"🎉 Розыгрыш начался! 🎉\n"
        f"Описание: {raffle_settings['description']}\n"
        f"Количество победителей: {raffle_settings['winners_count']}\n"
        "Нажмите кнопку ниже, чтобы участвовать.",
        reply_markup=reply_markup
    )

# Обработка данных из мини-приложения
async def handle_web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.message.from_user
    web_app_data = update.message.web_app_data.data
    logger.info(f"Данные из мини-приложения: {web_app_data}")

    # Добавляем пользователя в список участников
    if user.id not in participants:
        participants.append(user.id)
        logger.info(f"Пользователь {user.first_name} ({user.id}) участвует в розыгрыше.")
        await update.message.reply_text(
            f"🎉 {user.first_name}, вы успешно зарегистрировались на розыгрыш! 🎉"
        )
    else:
        await update.message.reply_text(
            f"🎉 {user.first_name}, вы уже участвуете в розыгрыше! 🎉"
        )

# Команда /endraffle
async def end_raffle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not raffle_settings["is_active"]:
        await update.message.reply_text("Розыгрыш не активен.")
        return

    if not participants:
        await update.message.reply_text("Нет участников для розыгрыша. 😢")
        logger.info("Розыгрыш завершен без участников.")
    else:
        winners = random.sample(participants, min(raffle_settings["winners_count"], len(participants)))
        winner_names = []
        for winner_id in winners:
            winner = await context.bot.get_chat(winner_id)
            winner_names.append(f"{winner.first_name} (@{winner.username})")
        logger.info(f"Победители розыгрыша: {', '.join(winner_names)}")
        await update.message.reply_text(
            f"🎉 Победители: {', '.join(winner_names)}! 🎉\n"
            "Поздравляем! 🎁"
        )
        participants.clear()
        raffle_settings["is_active"] = False

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Ошибка: {context.error}")

def main() -> None:
    # Вставьте сюда ваш токен
    TOKEN = "7868683592:AAEAjCPYx1u9LUlsuP32fx29nuSAFBYJtOI"

    # Создаем Application
    application = Application.builder().token(TOKEN).build()

    # Регистрируем команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setraffle", set_raffle))
    application.add_handler(CommandHandler("publishraffle", publish_raffle))
    application.add_handler(CommandHandler("endraffle", end_raffle))

    # Регистрируем обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Регистрируем обработчик данных из мини-приложения
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

    # Регистрируем обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    logger.info("Бот запущен и готов к работе.")
    application.run_polling()

if __name__ == '__main__':
    main()