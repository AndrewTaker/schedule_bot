import datetime
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from schedule import get_file, schedule_prettify
from utilities import get_tomorrow, get_week, as_datetime

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')


async def today(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Today's schedule."""
    schedule = get_file()
    today = datetime.datetime.strftime(
        datetime.datetime.today().date(), '%d.%m.%y'
    )
    result = 'Ничего не нашёл. Скорее всего, сегодня воскресенье'
    for data in schedule:
        if data['date'] == today:
            result = schedule_prettify(data)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result,
        parse_mode='html'
    )


async def tomorrow(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Tomorrow's schedule."""
    schedule = get_file()
    tomorrow = get_tomorrow()
    result = 'Ничего не нашёл. Скорее всего, завтра воскресенье'
    for data in schedule:
        if data['date'] == tomorrow:
            result = schedule_prettify(data)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result,
        parse_mode='html'
    )


async def week(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """This week's schedule."""
    schedule = get_file()
    current_week = get_week()
    result = ''
    for data in schedule:
        if as_datetime(data['date']).isocalendar().week == current_week:
            result += schedule_prettify(data)
            result += '🌚🌚🌚🌚🌚🌚🌚🌚🌚🌚🌚🌚\n\n'
    print(result)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result,
        parse_mode='html',
    )


async def next_week(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Next week's schedule."""
    schedule = get_file()
    next_week = get_week() + 1
    result = ''
    for data in schedule:
        if as_datetime(data['date']).isocalendar().week == next_week:
            result += schedule_prettify(data)
            result += '🌚🌚🌚🌚🌚🌚🌚🌚🌚🌚🌚🌚\n\n'

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result,
        parse_mode='html',
    )


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    today_handler = CommandHandler('today', today)
    tomorrow_handler = CommandHandler('tomorrow', tomorrow)
    week_handler = CommandHandler('week', week)
    next_week_handler = CommandHandler('next_week', next_week)

    application.add_handler(today_handler)
    application.add_handler(tomorrow_handler)
    application.add_handler(week_handler)
    application.add_handler(next_week_handler)
    application.run_polling()
