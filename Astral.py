import time
import requests
from bs4 import BeautifulSoup as BS4
import xml.etree.ElementTree as ET
import json
import config
from datetime import datetime
import os
import astral_function
import csv
from email_mes import send_email

def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))

    start = datetime.now()

    # Создаем сессию
    session = requests.Session()

    # Отправляем первый запрос (не обязательно)
    session.get('https://astralpool.ru/', headers=config.HEADERS_UA)

    # Данные пост запроса для входа в аккаунт
    data = {
        'login': 'sbkcompany',
        'password': 'sbkcompany778',
        'check': 'on'
    }

    # Авторизация
    session.post('https://astralpool.ru/bitrix/services/main/ajax.php?c=dev:popup.auth&action=auth&mode=class', headers=config.HEADERS_UA, data=data)

    r = session.get('https://astralpool.ru/personal/')
    soup = BS4(r.text, 'lxml')

    # Получаем код страницы со списком групп товаров
    conts = soup.find('select', class_='js-section').find_all('option')
    # print(conts)

    new_tovar = 0
    update_tovar = 0

    # Получаем список сохраненных id групп
    ALL_groups = astral_function.get_all_groups()
    print(f'ALL_groups - {ALL_groups}')

    # Получаем список всех товаров от поставщика АО Астрал
    ALL_tovar = astral_function.get_all_tovar_Astral()

    for cont in conts[1::]:
        I = 0

        # Проверяем является ли выбранный элемент группой или подгруппой
        grop_name_split = cont.text.strip().split('.')
        print(grop_name_split)
        if len(grop_name_split) == 2:
            name_lvl1_grop = grop_name_split[1].strip()
            lvl = '1'
            print(1)
        elif len(grop_name_split) == 3:
            name_lvl2_grop = grop_name_split[2].strip()
            lvl = '2'
            print(2)
        else:
            print("ERERER")

        # Ссылка на скачивание файла
        href_grop = f'https://astralpool.ru/personal/?export=csv&section_id={cont.get("value")}'

        # Получаем последний id группы первого уровня
        if lvl == '1':
            # Если группый нет в списке со всеми группами, создаем ее
            if name_lvl1_grop not in ALL_groups['lvl1']:
                last_id_lvl1 = astral_function.create_group(name_lvl1_grop, ALL_groups['id_Astral'])
                # print(last_id_lvl1)
                # print('lvl1')
            # Если группа есть, то получаем ее id
            else:
                last_id_lvl1 = ALL_groups['lvl1'][name_lvl1_grop]
                # print(f'Last - {last_id_lvl1}')

        # Получаем последний id группы второго уровня
        elif lvl == '2':
            if name_lvl2_grop not in ALL_groups['lvl2']:
                last_id_lvl2 = astral_function.create_group(name_lvl2_grop, last_id_lvl1)
                print('lvl2')
            else:
                last_id_lvl2 = ALL_groups['lvl2'][name_lvl2_grop]
                print(f'Last - {last_id_lvl2}')

            print(f'name_lvl2_grop - {name_lvl2_grop}')

            # Создаем файл данных
            astral_function.get_csv_file(session, href_grop, name_lvl2_grop)
            print('11111')


            # Читаем файл
            with open(os.path.join(dir_path, f'{name_lvl2_grop}.csv'), 'r', encoding='utf-8') as file:
                reader_r = csv.reader(file, delimiter=';')
                print('22222')

                # Проверяем на актульность файлы, если нет в списке, то добавляем в архив
                archive_tovar = astral_function.archive_offer(reader_r, name_lvl1_grop, name_lvl2_grop)
                print('33333')

            with open(os.path.join(dir_path, f'{name_lvl2_grop}.csv'), 'r', encoding='utf-8') as file:
                print('44444')
                reader = csv.reader(file, delimiter=';')
                print('55555')
                i = 0
                for row in reader:
                    if 'Артикул' in row[0]:
                        continue

                    if row[0] == '\ufeff':
                        break

                    if i >= 10:
                        break
                    i += 1
                    I += 1
                    print(f"I - {I} -> row[0] - {row[0]}")

                    # Читаем словарь уже добавленных товаров
                    with open(os.path.join(dir_path, f'Astral_data.json'), 'r') as file:
                        Astral_data = json.load(file)

                    # !!! NEW !!!
                    if name_lvl2_grop == 'Химия для бассейнов':
                        # !!! NEW !!!
                        ratio = astral_function.determine_ratio(row[1])
                        print(f"{ratio} = {row[1]}")
                    else:
                        ratio = 1

                    # !!! NEW !!!
                    row_dict = astral_function.form_dict_data(row, ratio)  # Создаем словарь данных одного товара
                    # print(row_dict)

                    data = astral_function.create_data_post(row_dict, last_id_lvl2)  # Формируем данные запроса на основе полученных данных

                    # Проверка на существование товара в МС
                    if str(row[0]).strip() in ALL_tovar:
                        chek_dif = 0

                        # Проверяем, изменилась ли цена товара, если изменилась, то отправляем запрос на изменение данных в МС
                        if row_dict["buyPrice"] != ALL_tovar[str(row[0]).strip()]['buyPrice']:
                            chek_dif = 1
                        if row_dict["minPrice"] != ALL_tovar[str(row[0]).strip()]['rrc']:
                            chek_dif = 1
                        if row_dict["priseSale"] != ALL_tovar[str(row[0]).strip()]['CTPZ']:
                            chek_dif = 1

                        if chek_dif != 0:
                            data_put = astral_function.create_data_put(row_dict)
                            r = requests.put(
                                f"https://online.moysklad.ru/api/remap/1.2/entity/product/{ALL_tovar[str(row[0]).strip()]['id']}",
                                headers=config.HEADERS_json, data=data_put)
                            update_tovar += 1
                        continue

                    # Проверяем, был ли товар уже добавлен
                    if row_dict["Article"] in Astral_data:
                        chek_dif = 0

                        # Проверяем, изменилась ли цена товара, если изменилась, то отправляем запрос на изменение данных в МС
                        if row_dict["buyPrice"] != Astral_data[row_dict["Article"]]['buyPrice']:
                            Astral_data[row_dict["Article"]]['buyPrice'] = row_dict["buyPrice"]
                            chek_dif = 1
                        if row_dict["minPrice"] != Astral_data[row_dict["Article"]]['minPrice']:
                            Astral_data[row_dict["Article"]]['minPrice'] = row_dict["minPrice"]
                            chek_dif = 1

                        if chek_dif != 0:  # запрос на изменение данных в МС
                            r = requests.put(
                                f"https://online.moysklad.ru/api/remap/1.2/entity/product/{Astral_data[row_dict['Article']]['ID']}",
                                headers=config.HEADERS_json, data=data)
                            update_tovar += 1

                    # Если товара нет в МС, то добавляем его
                    else:
                        r = requests.post('https://online.moysklad.ru/api/remap/1.2/entity/product',
                                          headers=config.HEADERS_json,
                                          data=data)
                        try:
                            Astral_data[f'{row_dict["Article"]}'] = {
                                'ID': r.json()['id'],
                                'name': row_dict["Name"],
                                'buyPrice': row_dict["buyPrice"],
                                'minPrice': row_dict["minPrice"]
                            }
                            new_tovar += 1
                        except:
                            print('ERROR - 139')
                            print(r.text)

                    # Перезаписываем словарь хранения измененных и записанных товаров в МС
                    # with open(os.path.join(dir_path, f'Astral_data.json'), 'w') as file:
                    #     json.dump(Astral_data, file, indent=3)
        # print()
        time.sleep(10)

    stop = datetime.now()

    log_mes = f'-- {start.strftime("%d-%m-%Y %H:%M")} -- {stop.strftime("%d-%m-%Y %H:%M")} -- ' \
              f'new = {new_tovar} -- update = {update_tovar} -- archive = {archive_tovar}'


    # with open(os.path.join(dir_path, f'LOG_astral.txt'), 'a') as file:
    #     file.write(f'{log_mes}\n')

    send_email(config.Subjects_aquapolis, update_tovar, new_tovar, archive_tovar, start, stop)

if __name__ == '__main__':
    main()

