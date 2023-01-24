import time

import requests
from bs4 import BeautifulSoup as BS4
import xml.etree.ElementTree as ET
import json
import config
from datetime import datetime
import Aquapolis_function
import os
import csv
from email_mes import send_email

def main():
    dir_path = os.path.dirname(os.path.abspath(__file__))

    start = datetime.now()

    # Создаем файл данных
    Aquapolis_function.get_xml_file()

    # Получаем список сохраненных id групп
    ALL_groups = Aquapolis_function.get_all_groups()

    # Получаем список всех товаров от поставщика АО Астрал
    ALL_tovar = Aquapolis_function.get_all_tovar_aquapolis()

    # Читаем файл
    tree = ET.parse(os.path.join(dir_path, f'aquapolis.xml'))
    root = tree.getroot()

    # Получаем карту категорий из файла
    maps_cat = Aquapolis_function.maps_categories(root)

    # Проверяем на актульность файлы, если нет в списке, то добавляем в архив
    archive_tovar = Aquapolis_function.archive_offer(root)

    new_tovar = 0
    update_tovar = 0
    i = 0

    for offer in root.find('shop').find('offers'):
        control_new = 0
        # if i > 19:
        #     break

        i += 1

        name = offer.find('name').text.strip()
        categorys_Id = offer.findall('categoryId')#.text.strip()
        cat_ids = []
        for category_Id in categorys_Id:
            cat_ids.append(int(category_Id.text.strip()))


        if len(cat_ids) != 0:
            cat_ids = max(cat_ids)
            # print(f"{cat_ids} - {name}")

            # Получаем путь до нужной категории
            path_cat = Aquapolis_function.create_path_categories(cat_ids, maps_cat)
            # print(path_cat)

            # if len(path_cat) == 2:
            try:
                if path_cat['lvl1']['name'] not in ALL_groups['lvl1']:
                    # print(111111111)
                    last_id_lvl1 = Aquapolis_function.create_group(path_cat['lvl1']['name'], ALL_groups['id_Aquapolis'])
                    ALL_groups['lvl1'][path_cat['lvl1']['name']] = last_id_lvl1
                else:
                    # print(222222222)
                    last_id_lvl1 = ALL_groups['lvl1'][path_cat['lvl1']['name']]
                last_id = last_id_lvl1

                if path_cat['lvl2']['name'] not in ALL_groups['lvl2']:
                    # print(333333333)
                    last_id_lvl2 = Aquapolis_function.create_group(path_cat['lvl2']['name'], last_id_lvl1)
                    ALL_groups['lvl2'][path_cat['lvl2']['name']] = last_id_lvl2
                else:
                    # print(444444444)
                    last_id_lvl2 = ALL_groups['lvl2'][path_cat['lvl2']['name']]
                last_id = last_id_lvl2

                if path_cat['lvl3']['name'] not in ALL_groups['lvl3']:
                    # print(333333333)
                    last_id_lvl3 = Aquapolis_function.create_group(path_cat['lvl3']['name'], last_id_lvl2)
                    ALL_groups['lvl3'][path_cat['lvl3']['name']] = last_id_lvl3
                else:
                    # print(444444444)
                    last_id_lvl3 = ALL_groups['lvl3'][path_cat['lvl3']['name']]
                last_id = last_id_lvl3
            except KeyError:
                pass

            # print(last_id)

        else:
            continue

        # Читаем словарь уже добавленных товаров
        with open(os.path.join(dir_path, f'Aquapolis_data.json'), 'r') as file:
            Aquapolis_data = json.load(file)

        row_dict = Aquapolis_function.form_dict_data(offer)  # Создаем словарь данных одного товара

        data = Aquapolis_function.create_data_post(row_dict, '1', last_id)    # Формируем данные запроса на основе полученных данных

        # Ищем артикул
        Article = ''
        params = offer.findall('param')
        for param in params:
            if str(param.get('name')) == 'sku':
                Article = param.text.strip()
                break
        print(f'I = {i} -> Article = {Article}')
        if Article != '' and str(Article).strip() in ALL_tovar:
            # Проверяем, изменилась ли цена товара, если изменилась, то отправляем запрос на изменение данных в МС
            if row_dict["minPrice"] != ALL_tovar[str(Article).strip()]['rrc']:
                data_put = Aquapolis_function.create_data_put(row_dict)
                r = requests.put(
                    f"https://online.moysklad.ru/api/remap/1.2/entity/product/{ALL_tovar[str(Article).strip()]['id']}",
                    headers=config.HEADERS_json, data=data_put)
                update_tovar += 1

            elif row_dict["priseSale"] != ALL_tovar[str(Article).strip()]['CTPZ']:
                data_put = Aquapolis_function.create_data_put(row_dict)
                r = requests.put(
                    f"https://online.moysklad.ru/api/remap/1.2/entity/product/{ALL_tovar[str(Article).strip()]['id']}",
                    headers=config.HEADERS_json, data=data_put)
                update_tovar += 1
            continue

        # print(f'I = {i} -> Article = {Article}')


        # Проверяем, был ли довар уже добавлен
        if row_dict["Article"] in Aquapolis_data:
            # Проверяем, изменилась ли цена товара, если изменилась, то отправляем запрос на изменение данных в МС
            if row_dict["minPrice"] != Aquapolis_data[row_dict["Article"]]['minPrice']:
                Aquapolis_data[row_dict["Article"]]['minPrice'] = row_dict["minPrice"]

                r = requests.put(
                    f"https://online.moysklad.ru/api/remap/1.2/entity/product/{Aquapolis_data[row_dict['Article']]['ID']}",
                    headers=config.HEADERS_json, data=data.encode('utf-8'))
                update_tovar += 1

        # Если товара нет в МС, то добавляем его
        else:
            r = requests.post('https://online.moysklad.ru/api/remap/1.2/entity/product',
                              headers=config.HEADERS_json, data=data.encode('utf-8'))
            if 'Ошибка' in r.text:
                data = Aquapolis_function.create_data_post(row_dict, '2', last_id)
                r = requests.post('https://online.moysklad.ru/api/remap/1.2/entity/product',
                                  headers=config.HEADERS_json, data=data.encode('utf-8'))

            if 'Ошибка' in r.text:
                data = Aquapolis_function.create_data_post(row_dict, '3', last_id)
                r = requests.post('https://online.moysklad.ru/api/remap/1.2/entity/product',
                                  headers=config.HEADERS_json, data=data.encode('utf-8'))

            if 'Ошибка' in r.text:
                print(r.text)
                print(data)
                print()
                break

            Aquapolis_data[f'{row_dict["Article"]}'] = {  # Добаляем запись в словарь, для будующей фильтрации
                'ID': r.json()['id'],
                'name': row_dict["Name"],
                'minPrice': row_dict["minPrice"]
            }
            new_tovar += 1

        # print()
        # print()

        # Перезаписываем словарь хранения измененных и записанных товаров в МС
        with open(os.path.join(dir_path, f'Aquapolis_data.json'), 'w') as file:
            json.dump(Aquapolis_data, file, indent=3)

    stop = datetime.now()

    log_mes = f'-- {start.strftime("%d-%m-%Y %H:%M")} -- {stop.strftime("%d-%m-%Y %H:%M")} -- ' \
              f'new = {new_tovar} -- update = {update_tovar} -- archive = {archive_tovar}'


    with open(os.path.join(dir_path, f'LOG_aquapolis.txt'), 'a') as file:
        file.write(f'{log_mes}\n')

    send_email(config.Subjects_aquapolis, update_tovar, new_tovar, archive_tovar, start, stop)


if __name__ == '__main__':
    main()