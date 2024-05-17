import logging
import paramiko
import re, os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
import psycopg2
from psycopg2 import Error

load_dotenv()

token = os.getenv('TOKEN')

rm_host = os.getenv('RM_HOST')
rm_port = os.getenv('RM_PORT')
rm_user = os.getenv('RM_USER')
rm_password = os.getenv('RM_PASSWORD')

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_port = os.getenv('DB_PORT')
db_host = os.getenv('DB_HOST')
db_database = os.getenv('DB_DATABASE')



logging.basicConfig(
    filename='./logs/logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)

logger = logging.getLogger(__name__)


def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')
    logger.info(f"Пользователь {user.full_name} начал общение.")

def helpCommand(update: Update, context):
    update.message.reply_text(
                              "/start - начать общение с ботом.\n" +
                              "/find_phone_number - найти телефонные номера в тексте.\n" +
                              "/find_email - найти email-адреса в тексте.\n" +
                              "/verify_password - проверить пароль на сложность.\n" +
                              "/get_release - информация о релизе.\n" +
                              "/get_uname - информация об архитектуре процессора, имени хоста системы и версии ядра.\n" +
                              "/get_uptime - информация о времени работы.\n" +
                              "/get_df - информация о состоянии файловой системы.\n" +
                              "/get_free - информация о состоянии оперативной памяти.\n" +
                              "/get_mpstat - информация о производительности системы.\n"+
                              "/get_w - информация о работающих в данной системе пользователях.\n"+
                              "/get_auths - последние 10 входов в систему.\n"+
                              "/get_critical - последние 5 критических события.\n"+
                              "/get_ps - информация о запущенные процессах.\n"+
                              "/get_ss - информация об используемых портах.\n"+
                              "/get_apt_list [packet] - информация об установленных пакетах.\n"+
                              "/get_services - информация о запущенных процессах.\n"+
                              "/help - вывести этот список.\n"+
                              "/get_repl_logs - чтобы получить логи о репликации БД.\n"+
                              "/get_emails - вывести почтовые адреса из БД.\n"+
                              "/get_phone_numbers - вывести телефонные номера из БД."
                              )
    logger.info("Пользователь запросил помощь")


def ssh_command(command):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=rm_host, username=rm_user, password=rm_password, port=rm_port)
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read() + stderr.read()
        client.close()
        return data.decode()
    except Exception as e:
        logger.error(f"Ошибка при исполнении команды '{command}': {str(e)}")
        return None

def execute_and_reply(update: Update, context, command, success_message):
    data = ssh_command(command)
    if data:
        update.message.reply_text(data)
        logger.info(success_message)
    else:
        update.message.reply_text(f"Ошибка во время исполнения команды: '{command}'.")
    

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска электронных почт: ')

    return 'findEmail'

def findEmail(update: Update, context):
    try:
        user_input = update.message.text
        emailRegex = re.compile(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+)')
        emailList = emailRegex.findall(user_input)
        if not emailList:
            update.message.reply_text('Электронные почты не найдены')
            logger.info("Электронные почты не найдены.")
            return
        emails = ''
        for i in range(len(emailList)):
            emails += f'{i+1}. {emailList[i]}\n'
        context.user_data['email_list'] = emailList
        update.message.reply_text('Найдены следующие электронные почты:\n' + emails +  
                                  '\nХотите записать их в базу данных? (да/нет)')
        logger.info("Найдены электронные почты и отправлены пользователю.")

        return 'confirm_email'
    except Exception as e:
        update.message.reply_text("Произошла ошибка при поиске электронных почт.")
        logger.error(f"Ошибка в функции поиска электронных почт: {str(e)}")


def confirm_email(update: Update, context):
    try:
        user_response = update.message.text.lower()
        if user_response == 'да':
            emailList = context.user_data['email_list']
            # Подключение к базе данных PostgreSQL
            connection = psycopg2.connect(user=db_user,
                                password=db_password,
                                host=db_host,
                                port=db_port, 
                                database=db_database)
            cursor = connection.cursor()
            for email in emailList:
                print(email)
                cursor.execute(f"INSERT INTO email(email) VALUES ('{email}')")
            connection.commit()
            cursor.close()
            connection.close()
            update.message.reply_text('Email успешно записаны в базу данных.')
            logger.info("Email успешно записаны в базу данных.")
        else:
            update.message.reply_text('Данные не были записаны в базу данных.')
            logger.info("Пользователь отказался от записи email в базу данных.")   
        del context.user_data['email_list']
        return ConversationHandler.END
    except Exception as e:
        update.message.reply_text("Произошла ошибка при записи данных в базу данных.")
        logger.error(f"Ошибка при записи данных в базу данных: {str(e)}")

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'


def findPhoneNumbers (update: Update, context):
    try:
        user_input = update.message.text 
        phoneNumRegex = re.compile(r'(?:(?:8|\+7)[\- ]?)(?:\(?\d{3}\)?[\- ]?)[\d\- ]{7,9}')
        phoneNumberList = phoneNumRegex.findall(user_input)
        if not phoneNumberList: 
            update.message.reply_text('Телефонные номера не найдены')
            logger.info("Телефонные номера не найдены.")
            return 
        phoneNumbers = ''
        for i in range(len(phoneNumberList)):
            phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'
        update.message.reply_text('Найдены следующие телефонные номера:\n' + phoneNumbers +
                                  '\nХотите записать их в базу данных? (да/нет)')
        logger.info("Найдены телефонные номера и отправлены пользователю.")
        context.user_data['phone_number_list'] = phoneNumberList

        return 'confirm_phone_number'
    except Exception as e:
        update.message.reply_text("Произошла ошибка при поиске телефонных номеров.")
        logger.error(f"Ошибка в функции поиска телефоннSых номеров: {str(e)}")


def confirm_phone_number(update: Update, context):
    try:
        user_response = update.message.text.lower()
        if user_response == 'да':
            phoneNumberList = context.user_data['phone_number_list']
            connection = psycopg2.connect(user=db_user,
                                password=db_password,
                                host=db_host,
                                port=db_port, 
                                database=db_database)
            cursor = connection.cursor()
            for phone_number in phoneNumberList:
                cursor.execute("INSERT INTO phone(phone_number) VALUES (%s)", (phone_number,))
            connection.commit()
            cursor.close()
            connection.close()
            update.message.reply_text('Номера телефонов успешно записаны в базу данных.')
            logger.info("Номера телефонов успешно записаны в базу данных.")
        else:
            update.message.reply_text('Данные не были записаны в базу данных.')
            logger.info("Пользователь отказался от записи номеров телефонов в базу данных.")
        # Очистка данных из контекста
        del context.user_data['phone_number_list']
        return ConversationHandler.END
    except Exception as e:
        update.message.reply_text("Произошла ошибка при записи данных в базу данных.")
        logger.error(f"Ошибка при записи данных в базу данных: {str(e)}")

def verifyPassCommand(update: Update, context):
    update.message.reply_text('Введите пароль: ')

    return 'verifyPass'


def verifyPass(update: Update, context):
    try:
        user_input = update.message.text
        PassRegex = re.compile(r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()])(?!.*\s).{8,}$")
        PassList = PassRegex.findall(user_input)
        if PassList:
            update.message.reply_text('Пароль сложный')
            logger.info("Пароль успешно проверен и является сложным.")
        else:
            update.message.reply_text('Пароль простой')
            logger.info("Пароль успешно проверен и является простым.")
        return ConversationHandler.END
    except Exception as e:
        update.message.reply_text("Произошла ошибка при проверке пароля.")
        logger.error(f"Ошибка в проверке пароля: {str(e)}")


def get_release(update: Update, context):
    execute_and_reply(update, context, 'lsb_release -a', "Информация о версии успешно получена и отправлена пользователю.")

def get_uname(update: Update, context):
    execute_and_reply(update, context, 'uname -a', "Информация об архитектуре процессора успешно получена и отправлена пользователю.")

def get_uptime(update: Update, context):
    execute_and_reply(update, context, 'uptime', "Информация о времени работы успешно получена и отправлена пользователю.")

def get_df(update: Update, context):
    execute_and_reply(update, context, 'df -h', "Информация о состоянии файловой системы успешно получена и отправлена пользователю.")

def get_free(update: Update, context):
    execute_and_reply(update, context, 'free -h', "Информация о состоянии памяти успешно получена и отправлена пользователю.")

def get_mpstat(update: Update, context):
    execute_and_reply(update, context, 'mpstat', "Информация о производительности системы успешно получена и отправлена пользователю.")

def get_w(update: Update, context):
    execute_and_reply(update, context, 'w', "Информация о пользователях успешно получена и отправлена пользователю.")

def get_auths(update: Update, context):
    execute_and_reply(update, context, 'last -n 10', "Информация о последних входах успешно получена и отправлена пользователю.")

def get_critical(update: Update, context):
    execute_and_reply(update, context, 'journalctl -p crit -n 5', "Информация о критических событиях успешно получена и отправлена пользователю.")

def get_ps(update: Update, context):
    execute_and_reply(update, context, 'ps au | head -n 10', "Информация о запущенных процессах успешно получена и отправлена пользователю.")

def get_ss(update: Update, context):
    execute_and_reply(update, context, 'ss -tuln', "Информация об используемых портах успешно получена и отправлена пользователю.")

def get_services(update: Update, context):
    execute_and_reply(update, context, 'systemctl list-units --type=service --state=running', "Информация о запущенных службах успешно получена и отправлена пользователю.")


def get_apt_list(update: Update, context):
    try:
        user_input = update.message.text.split()
        if len(user_input) == 1:
            command = 'dpkg -l | head -n 10'
        else:
            package_name = user_input[1]
            command = f'dpkg -l | grep {package_name}'
        execute_and_reply(update, context, command, "Информация об установленных пакетах успешно получена и отправлена пользователю.")
    except Exception as e:
        update.message.reply_text("Произошла ошибка при получении информации об установленных пакетах.")
        logger.error(f"Ошибка при получении информации об установленных пакетах: {str(e)}")


def get_repl_logs(update: Update, context):
    try:
        log_file_path = "/var/log/postgresql/postgresql.log"
        with open(log_file_path, 'r') as log_file:
            matching_lines = [line.strip() for line in log_file if 'repl' in line]
            last_matching_lines = matching_lines[-10:]
        response_message = '\n'.join(last_matching_lines)
        update.message.reply_text(response_message)
        logger.info("Последние 10 строк с содержанием 'repl' из лога PostgreSQL успешно отправлены пользователю.")
    except Exception as e:
        update.message.reply_text("Произошла ошибка при получении логов PostgreSQL.")
        logger.error(f"Ошибка при получении логов PostgreSQL: {str(e)}")


def get_emails(update: Update, context):
    try:
        # Установка соединения с базой данных
        connection = psycopg2.connect(user=db_user,
                                password=db_password,
                                host=db_host,
                                port=db_port, 
                                database=db_database)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM email;")
        email_data = cursor.fetchall()
        cursor.close()
        connection.close()
        if not email_data:
            update.message.reply_text("Нет данных об email адресах.")
        else:
            emails = ''
            for index, item in email_data:
                emails += f"{index}. {item}\n"
            update.message.reply_text(emails)
            logging.info("Данные о email адресах успешно отправлены пользователю.")
    except (Exception, Error) as error:
        update.message.reply_text("Произошла ошибка при получении данных о email адресах. %s" % error)
        logging.error("Ошибка при работе с PostgreSQL: %s" % error)


def get_phone_numbers(update: Update, context):
    try:
        connection = psycopg2.connect(user=db_user,
                                password=db_password,
                                host=db_host,
                                port=db_port, 
                                database=db_database)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM phone;")
        phone_data = cursor.fetchall()
        cursor.close()
        connection.close()
        if not phone_data:
            update.message.reply_text("Нет данных о телефонах.")
        else:
            phones = ''
            for index, item in phone_data:
                phones += f"{index}. {item}\n"
            update.message.reply_text(phones)
            logging.info("Данные о телефонах успешно отправлены пользователю.")
    except (Exception, Error) as error:
        update.message.reply_text("Произошла ошибка при получении данных о телефонах. %s" % error)
        logging.error("Ошибка при работе с PostgreSQL: %s" % error)


def main():
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher

    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('find_phone_number', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'confirm_phone_number': [MessageHandler(Filters.text & ~Filters.command, confirm_phone_number)],
        },
        fallbacks=[]
    )
	
    convHandlerEmails = ConversationHandler(
       entry_points=[CommandHandler('find_email', findEmailCommand)],
        states={
            'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'confirm_email': [MessageHandler(Filters.text & ~Filters.command, confirm_email)],
        },
        fallbacks=[]
    )
    convHandlerPass = ConversationHandler(
       entry_points=[CommandHandler('verify_password', verifyPassCommand)],
        states={
            'verifyPass': [MessageHandler(Filters.text & ~Filters.command, verifyPass)],
        },
        fallbacks=[]
    )
	# Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_apt_list", get_apt_list))
    dp.add_handler(CommandHandler("get_services", get_services))
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_emails", get_emails))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerEmails)
    dp.add_handler(convHandlerPass)
    
	# Запускаем бота
    updater.start_polling()

	# Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
