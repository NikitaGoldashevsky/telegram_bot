from telegram.ext import Updater, Filters, CommandHandler, ConversationHandler, MessageHandler
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
import requests
import datetime
import os


# Вспомогательный класс, предназначенный для временного хранения некоторых введеных пользователем данных
class Program:
    def __init__(self):
        self.username = ''
        self.desc = ''
        self.date = ''
        self.time = ''
        self.coords = ''
        self.scale = ''
        self.id = ''


# Описание функций программы:
def start(update, context):
    """
    Начинает диалог с пользователем, спрашивает его имя
    :param update:
    :param context:
    """

    # Проверяет вводил ли пользователь свое имя раньше
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
    """

    # Получает и заносит имя пользователя в базу данных
    program.username = update.message.text
    update.message.reply_text('Здравствуйте, ' + program.username)
    e.execute(f"""insert into user(id, name) values ({int(update.message.from_user.id)}, '{program.username}')""")

    return ConversationHandler.END


def change_name(update, context):
    """
    Спрашивает новое имя пользователя
    :param update:
    :param context:
    """

    # Проверяет не вводил ли пользователь свое имя раньше
    if no_name():
        update.message.reply_text("Пожалуйста представьтесь, написав /start")
        return ConversationHandler.END

    update.message.reply_text('Как к вам обращаться?\n'
                              '(/stop — оставить прежнее имя)')

    return 1


def name_response(update, context):
    """
    Заносит новое имя в базу данных
    :param update:
    """
    program.username = update.message.text

    # Изменение имени пользователя в базе данных
    update.message.reply_text('Ваше имя изменено, ' + program.username)
    e.execute(f"""insert into user(id, name) values ({int(update.message.from_user.id)}, '{program.username}')""")

    return ConversationHandler.END


def start_new(update, context):
    """
    Просит пользователя представиться, если он не сделал этого раньше и спрашивает описание нового напоминания
    :param update:
    :param context:
    """

    # Проверка, представился ли пользователь раньше
    if no_name():
        update.message.reply_text("Пожалуйста представьтесь, написав /start")
        return ConversationHandler.END

    # Вопрос об описании нового напоминания
    update.message.reply_text(
        f"{program.username}, какое описание напоминания?\n"
        "(/stop — отменить создание напоминания)")

    return 1


def new_first_response(update, context):
    """
    Спрашивает время напоминания
    :param update:
    :param context:
    """

    # Занесение описания в параметр класса Program
    program.desc = update.message.text

    update.message.reply_text(
        "В какое время напомнить?\n(например: 12:00)")

    return 2


def new_second_response(update, context):
    """
    Заносит напоминание в базу данных
    :param update:
    :param context:
    """

    reply = update.message.text

    # Проверка, является ли присланное пользователем сообщение корректным временем
    if len(reply) != 5 or reply[2] != ':' or not reply[0:2].isdigit() or not reply[3:].isdigit() or \
            int(reply[0:2]) not in range(0, 24) or int(reply[3:]) not in range(0, 60):
        # Если нет, новая попытка
        update.message.reply_text(
            "Неправильный формат времени, введите еще раз\n(пример: 12:00)")
        return 2

    program.time = reply

    update.message.reply_text(f"Напоминание с описанием: \"{program.desc}\"\n"
                              f"Будет воспроизведено в {program.time}")

    # Добавление нового напоминания в базу данных
    e.execute(f"""insert into reminders(user_id, desc, time) values (
{int(update.message.from_user.id)}, '{program.desc}', '{program.time}')""")

    return ConversationHandler.END


def send_message_job(context):
    """
    Отправляет все напоминания, соответствующие текущему времени
    :param context:
    """

    # Получение нужных напоминаний из базы данных
    data = e.execute(f"""
            select * from reminders where user_id == "{int(program.id)}"
            """).fetchall()

    # Прекращение работы функции, если напоминаний нет
    if not len(data):
        return

    for elem in data:

        # Проверка, является ли время напоминания текущим временем
        if elem[3] == str(datetime.datetime.now().time())[:5]:
            context.bot.send_message(context.job.context, text=elem[2])


def stop_new(update, context):
    """
    Завершает текущий диалог
    :param update:
    :param context:
    """

    update.message.reply_text("Создание напоминания отменено")

    return ConversationHandler.END


def stop_name(update, context):
    """
    Завершает текущий диалог
    :param update:
    :param context:
    """

    update.message.reply_text("Ваше имя останется прежним")

    return ConversationHandler.END


def start_delete(update, context):
    """
    Спрашивает номер напоминания, которое нужно удалить
    :param update:
    :param context:
    """

    update.message.reply_text(
        "Введите номер напоминания, которое хотите удалить")

    return 1


def delete_response(update, context):
    """
    Удаляет напоминание с этим номером
    :param update:
    :param context:
    """

    # Удаление напоминания, если не возникло исключений
    try:
        e.execute(f"""DELETE FROM reminders WHERE id={update.message.text}""")

    # OperationalError может возникнуть, если id не является integer-ом
    except OperationalError:
        update.message.reply_text('Введите порядковый номер нужного напоминания\n(узнать его можно с помощью /list)')

        # Новая попытка пользователю
        return 1

    # Если все проходит успешно, программа сообщает об этом пользователю
    else:
        update.message.reply_text('Удалено')

    return ConversationHandler.END


def stop_delete(update, context):
    """
    Завершает текущий диалог
    :param update:
    :param context:
    """

    update.message.reply_text("Ни одно напоминание не будет удалено")

    return ConversationHandler.END


def help(update, context):
    """
    Выводит список всех команд бота
    :param update:
    :param context:
    """

    # Вывод списка комманд
    update.message.reply_text("Команды бота:\n"
                              "/help — вывести список всех команд\n"
                              "/new — создать новое напоминание\n"
                              "/list — вывести список всех напоминаний\n"
                              "/delete — удалить выбранное напоминание\n"
                              "/map — получить схематичное изображение карты\n"
                              "/name — изменить ваше имя")

    return ConversationHandler.END


def list(update, context):
    """
    Выводит список всех созданных напоминаний
    :param update:
    :param context:
    """

    # Получение нужных напоминаний из базы данных
    data = e.execute(f"""
            select * from reminders where user_id == "{int(update.message.from_user.id)}"
            """).fetchall()

    # Проверка, есть ли напоминания в базе данных
    if len(data):
        update.message.reply_text(f'{program.username}, вот список всех созданных вами напоминаний:')

        # Отправка информации о каждом элементе списка data
        for elem in data:
            update.message.reply_text(f'{elem[0]}: {elem[2]} ({elem[3]})')

    # Сообщение об отсутствии напоминаний в базе данных
    else:
        update.message.reply_text('Вы не создали ни одного напоминания')

    return ConversationHandler.END


def no_name():
    """
    Проверяет, ввел ли пользователь свое имя
    :return: True или False
    """

    if program.username == '':
        return True
    return False


def pass_stop(update, context):
    """
    Выводит сообщение ниже
    :param update:
    :param context:
    """

    # Вывод этого сообщения нужен для тех функций,
    # которым нужно чтобы пользователь представился перед их использованием
    update.message.reply_text("Пожалуйста, напишите, как программе обращаться к вам")


def start_map(update, context):
    """
    Спрашивает координаты места
    :param update:
    :param context:
    """

    update.message.reply_text("Напишите координаты места\n(например, 37.677751,55.757718)")

    return 1


def map_first_response(update, context):
    """
    Спрашивает масштаб
    :param update:
    :param context:
    """

    # Сохранение координат в program.coords
    program.coords = update.message.text

    update.message.reply_text('Напишите масштаб\n(например, 0.003,0.003)')

    return 2


def map_second_response(update, context):
    """
    Отправляет изображение карты
    :param update:
    :param context:
    :return:
    """

    program.scale = update.message.text

    # Составление запроса
    map_request = f"http://static-maps.yandex.ru/1.x/?ll={program.coords}&" \
                  f"spn={program.scale}&l=map"
    chat_id = update.message.chat_id

    # Проверка корректности запроса
    response = requests.get(map_request)

    # Отправка полученного изображения
    if response.status_code == 200:
        context.bot.send_photo(chat_id, map_request)

    # Если запрос не был корректен, сообщение об ошибке
    else:
        context.bot.send_message(chat_id=chat_id, text='Произошла ошибка, попробуйте снова\n'
                                                       f'(код состояния запроса - {response.status_code})')

    return ConversationHandler.END


def stop_map(update, context):
    """
    Завершает текущий диалог
    :param update:
    :param context:
    """
    update.message.reply_text("Показ карты отменен")
    return ConversationHandler.END


def main():
    """
    Главная функция программы
    :return:
    """

    # Удаление старой базы данных и создание новой
    if os.path.exists("data.db"):
        os.remove("data.db")

    # Создание глобальной переменной "e" для взаимодействия с базой данных и создание самой базы данных
    global e
    e = create_engine("sqlite:///data.db")

    # Создание таблицы для id и имен пользователей
    e.execute("""
        create table user (
            id integer,
            name varchar
        )
    """)

    # Создание таблицы для напоминаний
    e.execute("""
                create table reminders (
                id integer primary key,
                user_id varchar,
                desc varchar,
                time varchar
            )
        """)

    # Чтение токена из файла not a token.txt
    with open('not a token.txt', 'r') as file:
        token = file.read()

    # Создание объектов updater и dispatcher
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    # Диалог, создающий новое напоминание
    new_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('new', start_new)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, new_first_response)],
            2: [MessageHandler(Filters.text & ~Filters.command, new_second_response)],
        },

        fallbacks=[CommandHandler('stop', stop_new)]
    )

    # Диалог, меняющий старое имя пользователя на новое
    name_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('name', change_name)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, name_response)],
        },

        fallbacks=[CommandHandler('stop', stop_name)]
    )

    # Диалог, отправляющий изборажение, полученное с помощью API Яндекс.Карт
    map_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('map', start_map)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, map_first_response)],
            2: [MessageHandler(Filters.text & ~Filters.command, map_second_response)],
        },

        fallbacks=[CommandHandler('stop', stop_map)]
    )

    # Диалог, удаляющий одно из напоминаний
    delete_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('delete', start_delete)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, delete_response)],
        },

        fallbacks=[CommandHandler('stop', stop_delete)]
    )

    # Диалог, начинающий общение с новым пользователем
    start_conv_handler = ConversationHandler(

        entry_points=[CommandHandler('start', start)],

        states={
            1: [MessageHandler(Filters.text & ~Filters.command, start_response)],
        },

        fallbacks=[CommandHandler('stop', pass_stop)]
    )

    # Добавление в диспетчер объектов типов ConverstaionHandler
    dp.add_handler(name_conv_handler)
    dp.add_handler(new_conv_handler)
    dp.add_handler(start_conv_handler)
    dp.add_handler(delete_conv_handler)
    dp.add_handler(map_conv_handler)

    # Добавление объектов CommandHandler
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("list", list))

    # Создание объекта вспомогательного класса Program
    global program
    program = Program()

    # Запуск работа бота
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
