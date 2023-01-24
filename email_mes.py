import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


dir_path = os.path.dirname(os.path.abspath(__file__))


# Отправка сообщения на почту gmail
def send_email(Subject, update_tovar, new_tovar, archive_tovar, start, stop):
    sender = 'dmitrymiloyanin@yandex.ru'   # адрес почты отправителя
    password = 'nzpolruvvekrrgeu'           # пароль из созданного приложения в настройках безопасноти
    # print('1')
    # Определяем порт к котором убудем подключаться
    # server = smtplib.SMTP("smtp.gmail.com", 587)
    server = smtplib.SMTP('smtp.yandex.ru', 587)
    # print(3)
    # server.ehlo(sender)
    server.starttls()
    # print(4)

    # авторизуемся на посте
    server.login(sender, password)
    # print(5)

    # Объявляем тело сообщения
    msg = MIMEMultipart()
    msg["From"] = sender                        # от куда идет сообщение
    msg["To"] = sender                          # куда идут сообщение
    msg["Subject"] = Subject  # тема сообщения

    # msg.attach(MIMEText(f'{Subject}!'))    # текст сообщения
    MSG = f"Обновлено цен: {update_tovar}\n" \
          f"Добавлено новых товаров: {new_tovar}\n" \
          f"Товаров перемещено в архив: {archive_tovar}\n" \
          f"Скрипт запущен: {start.strftime('%d-%m-%Y %H:%M')}\n" \
          f"Скрипт отработал: {stop.strftime('%d-%m-%Y %H:%M')}"
    msg.attach(MIMEText(f'{MSG}'))  # текст сообщения

    # Отправка сообщения
    server.sendmail(sender, 'mdu@sbk.group', msg.as_string())


