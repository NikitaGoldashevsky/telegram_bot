from telegram.ext import Updater, Filters, CommandHandler, ConversationHandler, MessageHandler
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import datetime
import os


class Program:
    def __init__(self):
        self.username = ''
        self.desc = ''
        self.date = ''
        self.time = ''
        self.coords = ''
        self.scale = ''
        self.id = ''


def start(update, context):
    """
    Начинает диалог с пользователем, спрашивает его имя
    :param update:
    :param context:
    :return:
    """
    if not no_name():
        update.message.reply_text("Вы уже представились. Для получения списка всех команд напишите /help")
        return ConversationHandler.END

    update.message.reply_text('Как к вам обращаться?')
    program.id = update.message.chat_id

    context.job_queue.run_repeating(send_message_job, 60, context=update.message.chat_id)

    return 1


def start_response(update, context):
    """
    Ответ на вопрос об имени пользователя
    :param update:
    :param context:
    :return:
    """
    program.username = update.message.text
    update.message.reply_text('Здравствуйте, ' + program.username)
    e.execute(f"""insert into user(id, name) values ({int(update.message.from_user.id)}, '{program.username}')""")

    return ConversationHandler.END


def change_name(update, context):
    if no_name():
        update.message.reply_text("Пожалуйста представьтесь, написав /start")
        return ConversationHandler.END

    update.message.reply_text('Как к вам обращаться?\n'
                              '(/stop — оставить прежнее имя)')

    return 1


def name_response(update, context):
    program.username = update.message.text

    update.message.reply_text('Ваше имя изменено, ' + program.username)
    e.execute(f"""insert into user(id, name) values ({int(update.message.from_user.id)}, '{program.username}')""")

    return ConversationHandler.END


def start_new(update, context):
    if no_name():
        update.message.reply_text("Пожалуйста представьтесь, написав /start")
        return ConversationHandler.END

    update.message.reply_text(
        f"{program.username}, какое описание напоминания?\n"
        "(/stop — отменить создание напоминания)")

    return 1


def new_first_response(update, context):
    program.desc = update.message.text

    update.message.reply_text(
        "В какое время напомнить?\n(например: 12:00)")

    return 2


def sayhi(context):
    context.bot.send_message(context.job.context, text="hi")


def new_second_response(update, context):
    reply = update.message.text

    if len(reply) != 5 or reply[2] != ':' or not reply[0:2].isdigit() or not reply[3:].isdigit() or \
            int(reply[0:2]) not in range(0, 24) or int(reply[3:]) not in range(0, 60):
        update.message.reply_text(
            "Неправильный формат времени, введите еще раз\n(пример: 12:00)")
        return 2

    program.time = reply

    update.message.reply_text(f"Напоминание с описанием: \"{program.desc}\"\n"
                              f"Будет воспроизведено в {program.time}")
    t = datetime.time(hour=int(program.time[:2]), minute=int(program.time[3:]))

    e.execute(f"""insert into reminders(user_id, desc, time) values (
{int(update.message.from_user.id)}, '{program.desc}', '{program.time}')""")

    return ConversationHandler.END


def send_message_job(context):
    data = e.execute(f"""
            select * from reminders where user_id == "{int(program.id)}"
            """).fetchall()
    if not len(data):
        return

    for elem in data:
        if elem[3] == str(datetime.datetime.now().time())[:5]:
            context.bot.send_message(context.job.context, text=elem[2])


def stop_new(update, context):
    update.message.reply_text("Создание напоминания отменено")
    return ConversationHandler.END


def stop_name(update, context):
    update.message.reply_text("Ваше имя останется прежним")
    return ConversationHandler.END


def start_delete(update, context):
    update.message.reply_text(
        "Введите номер напоминания, которое хотите удалить")

    return 1


def delete_response(update, context):
    try:
        e.execute(f"""DELETE FROM reminders WHERE id={update.message.text}""")
    except OperationalError:
        update.message.reply_text('Введите порядковый номер нужного напоминания\n(узнать его можно с помощью /list)')
        return 1
    else:
        update.message.reply_text('Удалено')

    return ConversationHandler.END


def stop_delete(update, context):
    update.message.reply_text("Ни одно напоминание не будет удалено")
    return ConversationHandler.END


def help(update, context):
    update.message.reply_text("Команды бота:\n"
                              "/help — вывести список всех команд\n"
                              "/new — создать новое напоминание\n"
                              "/list — вывести список всех напоминаний\n"
                              "/delete — удалить выбранное напоминание\n"
                              "/map — получить схематичное изображение карты\n"
                              "/name — изменить ваше имя")
    return ConversationHandler.END


def list(update, context):
    data = e.execute(f"""
            select * from reminders where user_id == "{int(update.message.from_user.id)}"
            """).fetchall()
    if len(data):
        update.message.reply_text(f'{program.username}, вот список всех созданных вами напоминаний:')
        for elem in data:
            update.message.reply_text(f'{elem[0]}: {elem[2]}, ({elem[3]})')
    else:
        update.message.reply_text('Вы не создали ни одного напоминания')

    return ConversationHandler.END


def no_name():
    if program.username == '':
        return True
    return False


def pass_stop(update, context):
    update.message.reply_text("Пожалуйста, напишите, как программе обращаться к вам")


def start_map(update, context):
    update.message.reply_text("Напишите координаты места\n(например, 37.677751,55.757718)")

    return 1


def map_first_response(update, context):
    program.coords = update.message.text

    update.message.reply_text('Напишите масштаб\n(например, 0.003,0.003)')

    return 2


def map_second_response(update, context):
    program.scale = update.message.text

    map_request = f"http://static-maps.yandex.ru/1.x/?ll={program.coords}&" \
                  f"spn={program.scale}&l=map"
    chat_id = update.message.chat_id

    updater.bot.send_photo(chat_id, map_request)

    return ConversationHandler.END


def stop_map(update, context):
    update.message.reply_text("Показ карты отменен")
    return ConversationHandler.END


def main():
    if os.path.exists("data.db"):
        os.remove("data.db")

    global e
    e = create_engine("sqlite:///data.db")
    e.execute("""
        create table user (
            id integer,
            name varchar
        )
    """)
    e.execute("""
                create table reminders (
                id integer primary key,
                user_id varchar,
                desc varchar,
                time varchar
            )
        """)

    with open('not a token.txt', 'r') as file:
        token = file.read()

    global updater
    updater = Updater(token, use_context=True)

    dp = updater.dispatcher
    jq = updater.job_queue

    # text_handler = MessageHandler(Filters.text, text)
    # dp.add_handler(text_handler)

    new_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('new', start_new)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, new_first_response)],
            2: [MessageHandler(Filters.text & ~Filters.command, new_second_response)],
        },

        fallbacks=[CommandHandler('stop', stop_new)]
    )

    name_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('name', change_name)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, name_response)],
        },

        fallbacks=[CommandHandler('stop', stop_name)]
    )

    map_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('map', start_map)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, map_first_response)],
            2: [MessageHandler(Filters.text & ~Filters.command, map_second_response)],
        },

        fallbacks=[CommandHandler('stop', stop_map)]
    )

    delete_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('delete', start_delete)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, delete_response)],
        },

        fallbacks=[CommandHandler('stop', stop_delete)]
    )

    start_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('start', start)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, start_response)],
        },

        fallbacks=[CommandHandler('stop', pass_stop)]
    )

    dp.add_handler(name_conv_handler)
    dp.add_handler(new_conv_handler)
    dp.add_handler(start_conv_handler)
    dp.add_handler(delete_conv_handler)
    dp.add_handler(map_conv_handler)
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("list", list))

    global program
    program = Program()

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
