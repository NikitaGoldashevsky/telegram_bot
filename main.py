from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler


class Program:
    def __init__(self):
        self.username = ''
        self.desc = ''
        self.time = ''


def text(update, context):
    update.message.reply_text('Пишите команды')


def start_new(update, context):
    update.message.reply_text(
        "Какое описание напоминания?")

    return 1


def first_response(update, context):
    program.desc = update.message.text

    update.message.reply_text(
        "В какое время напомнить?")

    return 2


def second_response(update, context):
    program.time = update.message.text

    update.message.reply_text(f"Напоминание с описанием: \"{program.desc}\"\n"
                              f"И временем воспроизведения {program.time} создано")
    return ConversationHandler.END


def stop(update, context):
    update.message.reply_text("Создание напоминания отменено")
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    text_handler = MessageHandler(Filters.text, text)
    dp.add_handler(text_handler)

    conv_handler = ConversationHandler(
        # Точка входа в диалог.
        entry_points=[CommandHandler('start', start_new)],

        states={
            # Функция читает ответ на первый вопрос и задаёт второй.
            1: [MessageHandler(Filters.text & ~Filters.command, first_response)],
            # Функция читает ответ на второй вопрос и завершает диалог.
            2: [MessageHandler(Filters.text & ~Filters.command, second_response)]
        },

        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(conv_handler)
    dp.add_handler(text_handler)

    global program
    program = Program()

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
