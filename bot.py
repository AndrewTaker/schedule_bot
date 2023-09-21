import datetime
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from schedule import (
    get_file,
    schedule_prettify,
    get_last_date_update,
    get_data,
    is_schedule_updated,
    download_file,
    clear_xlsx_files,
    WEBSITE_DATE_FORMAT
)
from utilities import (
    get_tomorrow,
    get_week,
    as_datetime,
    get_website_status_code,
    get_list_of_xlsx_files,
)

load_dotenv()
TOKEN: str = os.getenv('BOT_TOKEN')
SCHEDULE_CHECK_INTERVAL: int = 30 * 60


async def today(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Today's schedule."""
    schedule = get_file()
    today = datetime.datetime.strftime(
        datetime.datetime.today().date(), '%d.%m.%y'
    )
    result = 'Ничего не нашёл. Скорее всего, сегодня воскресенье.'
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


async def schedule_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback for jobque to check whether schedule updated or not."""
    current_schedule = get_data()
    last_update: str = datetime.datetime.strptime(
        get_last_date_update(),
        WEBSITE_DATE_FORMAT
    )
    if is_schedule_updated(current_schedule, last_update):
        download_file(current_schedule.url, current_schedule.date)
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=f'Обновили раписание: {last_update} '
        )


async def reminder(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Start wathing for schedule changes."""
    chat_id = update.message.chat_id
    name = update.effective_chat.full_name
    await context.bot.send_message(
        chat_id=chat_id,
        text='Напишу, как расписание изменится.'
    )
    context.job_queue.run_repeating(
        callback=schedule_job,
        interval=SCHEDULE_CHECK_INTERVAL,
        data=name,
        chat_id=chat_id
    )


async def health(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Check schedule and bot status."""
    message = ''
    message += get_last_date_update() + '\n'
    message += '\n'.join(get_list_of_xlsx_files()) + '\n'
    message += str(get_website_status_code())
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
    )


if __name__ == '__main__':
    clear_xlsx_files()
    schedule = get_data()
    download_file(schedule.url, schedule.date)
    application = ApplicationBuilder().token(TOKEN).build()

    today_handler = CommandHandler('today', today)
    tomorrow_handler = CommandHandler('tomorrow', tomorrow)
    week_handler = CommandHandler('week', week)
    next_week_handler = CommandHandler('next_week', next_week)
    reminder_handler = CommandHandler('reminder', reminder)
    health_check_handler = CommandHandler('health', health)

    application.add_handler(today_handler)
    application.add_handler(tomorrow_handler)
    application.add_handler(week_handler)
    application.add_handler(next_week_handler)
    application.add_handler(reminder_handler)
    application.add_handler(health_check_handler)

    application.run_polling()
