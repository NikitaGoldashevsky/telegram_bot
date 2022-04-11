from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler
from sqlalchemy import create_engine
import os


class Program:
    def __init__(self):
        self.username = ''
        self.desc = ''
        self.date = ''
        self.time = ''


def start(update, context):
    if not no_name():
        update.message.reply_text("Вы уже представились. Для получения списка всех команд напишите /help")
        return ConversationHandler.END

    update.message.reply_text('Как к вам обращаться?')

    return 1


def start_response(update, context):
    program.username = update.message.text
    update.message.reply_text('Здравствуйте, ' + program.username)
    e.execute(f"""insert into user(id, name) values ({int(update.message.from_user.id)}, '{program.username}')""")

    return ConversationHandler.END


# def text(update, context):
#    update.message.reply_text('Пишите команды')


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
        "В какой день напомнить?\n(например: 31.01)")

    return 2


def new_second_response(update, context):
    reply = update.message.text

    if len(reply) != 5 or reply[2] != '.' or not reply[0:2].isdigit() or not reply[3:].isdigit() or \
            int(reply[0:2]) not in range(1, 32) or int(reply[3:]) not in range(1, 13):
        update.message.reply_text(
            "Неправильный формат даты, введите еще раз\n(пример: 31.01)")
        return 2

    program.date = reply

    update.message.reply_text(
        "В какое время напомнить?\n(например: 12:00)")

    return 3


def new_third_response(update, context):
    reply = update.message.text

    if len(reply) != 5 or reply[2] != ':' or not reply[0:2].isdigit() or not reply[3:].isdigit() or \
            int(reply[0:2]) not in range(0, 24) or int(reply[3:]) not in range(0, 60):
        update.message.reply_text(
            "Неправильный формат времени, введите еще раз\n(пример: 12:00)")
        return 3

    program.time = reply

    update.message.reply_text(f"Напоминание с описанием: \"{program.desc}\"\n"
                              f"Будет воспроизведено {program.date} "
                              f"в {program.time}")
    return ConversationHandler.END


def stop_new(update, context):
    update.message.reply_text("Создание напоминания отменено")
    return ConversationHandler.END


def stop_name(update, context):
    update.message.reply_text("Ваше имя останется прежним")
    return ConversationHandler.END


def help(update, context):
    update.message.reply_text("Команды бота:\n"
                              "/help — вывести список всех команд\n"
                              "/new — создать новое напоминание\n"
                              "/name — изменить ваше имя")
    return ConversationHandler.END


def no_name():
    if program.username == '':
        return True
    return False


def pass_stop(update, context):
    update.message.reply_text("Пожалуйста, напишите, как программе обращаться к вам")


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

    updater = Updater('5269699771:AAGLPqG-A7q_2lHTYrwZ1INLfMwk6SyKH0M', use_context=True)

    dp = updater.dispatcher

    # text_handler = MessageHandler(Filters.text, text)
    # dp.add_handler(text_handler)

    new_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('new', start_new)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, new_first_response)],
            2: [MessageHandler(Filters.text & ~Filters.command, new_second_response)],
            3: [MessageHandler(Filters.text & ~Filters.command, new_third_response)]
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
    dp.add_handler(CommandHandler("help", help))

    global program
    program = Program()

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
