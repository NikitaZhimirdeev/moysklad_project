import requests
import base64
import config
import os
import json

dir_path = os.path.dirname(os.path.abspath(__file__))


# Проверяем на актульность файлы, если нет в списке, то добавляем в архив
def archive_offer(reader, name_lvl1_grop, name_lvl2_grop):
    Articles = []
    # i = 0
    archive_tovar = 0
    i = 0

    # Собираем список артикулов из актуального файла
    for row in reader:
        if 'Артикул' in row[0]:
            continue

        if i > 100:
            break
        i += 1

        Article = row[0]
        # print(Article)
        Articles.append(Article)


    # Получаем список товаров с МС
    r = requests.get("https://online.moysklad.ru/api/remap/1.2/entity/product", headers=config.HEADERS)

    r_j = r.json()['rows']

    # Ищем артикулы товаров которые уже добавлены в МС
    for row in r_j:
        # Выбираем необходимую группу
        # print(row['pathName'])
        if row['pathName'] == f'Новые товары/Astral/{name_lvl1_grop}/{name_lvl2_grop}':
            # print(22222)
            article = row['article']
            # print(article)

            # Проверяем, есть ли артикул в актульном списке, если его нет, то помещаем в архив
            if article not in Articles:

                data = '{"archived": true}'.encode('utf-8')  #

                # Запрос на поммещенение товара в архив
                rrr = requests.put(f'https://online.moysklad.ru/api/remap/1.2/entity/product/{row["id"]}',
                                   headers=config.HEADERS_json, data=data)

                archive_tovar += 1

    return archive_tovar

# Скачиваем csv файл
def get_csv_file(session, url, name_file):
    # Запрос скачает файл
    file = session.get(url)

    # Сохраняем файл
    with open(os.path.join(dir_path, f'{name_file}.csv'), 'wb') as f:
        f.write(file.content)

# !!! NEW !!! vat
# Формируем данные запроса на основе полученных данных
def create_data_post(row_dict, id_group):
    data = '{' \
           f'"article": "{row_dict["Article"]}",' \
           f'"name": "{row_dict["Name"]}",' \
           f'"description": "{row_dict["Description"]}",' \
           f'"vat": 20,' \
           '"uom": {' \
           '"meta": {' \
           '"href": "https://online.moysklad.ru/api/remap/1.2/entity/uom/19f1edc0-fc42-4001-94cb-c9ec9c62ec10",' \
           '"metadataHref": "https://online.moysklad.ru/api/remap/1.2/entity/uom/metadata",' \
           '"type": "uom",' \
           '"mediaType": "application/json"}},' \
           '"buyPrice":{' \
           f'"value": {round(float(row_dict["buyPrice"]), 2) * 100}' \
           '},' \
           '"salePrices": [' \
               '{' \
               f'"value": {round(float(row_dict["minPrice"]), 2) * 100},' \
               '"priceType": {' \
               '"meta": {' \
               f'"href": "https://online.moysklad.ru/api/remap/1.2/context/companysettings/pricetype/{config.RRC_POST}",' \
               '"type": "pricetype",' \
               '"mediaType": "application/json"' \
               '}}},' \
           '{' \
               f'"value": {round(float(row_dict["priseSale"]), 2) * 100},' \
               '"priceType": {' \
               '"meta": {' \
               f'"href": "https://online.moysklad.ru/api/remap/1.2/context/companysettings/pricetype/{config.CTPZ}",' \
               '"type": "pricetype",' \
               '"mediaType": "application/json"' \
               '}}}' \
           '],' \
           '"productFolder": {' \
           '"meta": {' \
           f'"href": "https://online.moysklad.ru/api/remap/1.2/entity/productfolder/{id_group}",' \
           '"metadataHref": "https://online.moysklad.ru/api/remap/1.2/entity/productfolder/metadata",' \
           '"type": "productfolder",' \
           '"mediaType": "application/json"}},' \
           '"supplier": {' \
           '"meta": {' \
           f'"href": "https://online.moysklad.ru/api/remap/1.2/entity/supplier/{config.supplier_Astral}",' \
           '"metadataHref": "https://online.moysklad.ru/api/remap/1.2/entity/counterparty/metadata",' \
           '"type": "counterparty",' \
           '"mediaType": "application/json"}},' \
           '"images": [' \
           '{' \
           f'"filename": "{row_dict["Article"]}",' \
           f'"content": "{row_dict["IMG"]}"' \
           '}]' \
           '}'.encode('utf-8')

    return data


# Формируем данные запроса на основе полученных данных для обновления
def create_data_put(row_dict):
    data = '{' \
           '"buyPrice":{' \
           f'"value": {round(float(row_dict["buyPrice"]), 2) * 100}' \
           '},' \
           '"salePrices": [' \
               '{' \
               f'"value": {round(float(row_dict["minPrice"]), 2) * 100},' \
               '"priceType": {' \
               '"meta": {' \
               f'"href": "https://online.moysklad.ru/api/remap/1.2/context/companysettings/pricetype/{config.RRC_POST}",' \
               '"type": "pricetype",' \
               '"mediaType": "application/json"' \
               '}}},' \
           '{' \
               f'"value": {round(float(row_dict["priseSale"]), 2) * 100},' \
               '"priceType": {' \
               '"meta": {' \
               f'"href": "https://online.moysklad.ru/api/remap/1.2/context/companysettings/pricetype/{config.CTPZ}",' \
               '"type": "pricetype",' \
               '"mediaType": "application/json"' \
               '}}}' \
           ']' \
           '}'.encode('utf-8')

    return data

# !!! NEW !!!
# словарь данных одного товара
def form_dict_data(row, ratio):
    row_dict = {}

    with open('k_firm.json', 'r') as file:  # !!! NEW !!!
        k_firm = json.load(file)

    name_group = row[8] # !!! NEW !!!
    if row[8] in k_firm:    # !!! NEW !!!
        K = (100 + k_firm[row[8]]['k'])/100
    else:
        K = 1


    row_dict['Article'] = row[0]
    try:
        row_dict['Name'] = row[1].replace('"', "'")
    except:
        print(f'WWWW - {row}')
        row_dict['Name'] = row[1].replace('"', "'")

    try:
        row_dict['Name'] = f"{k_firm[row[8]]['firm']} {row_dict['Name']}"
    except:
        pass
    row_dict['buyPrice'] = float(row[4]) * ratio # !!! NEW !!!
    row_dict['minPrice'] = float(row[6]) * ratio # !!! NEW !!!
    row_dict['priseSale'] = row_dict['minPrice'] * K # !!! NEW !!!
    row_dict['Description'] = row[2].replace("\n", "").replace('"', "'")

    # Преобразуем изображение в base64 (требование МС)
    try:
        r_img = requests.get(row[3], headers=config.HEADERS_UA)
        row_dict['IMG'] = str(base64.b64encode(r_img.content)).split("'")[1].split("'")[0]
    except:
        row_dict['IMG'] = ''

    return row_dict


# Получем список всех необходимых групп
def get_all_groups():
    r = requests.get('https://online.moysklad.ru/api/remap/1.2/entity/productfolder', headers=config.HEADERS)
    # print(r.text)
    rows = r.json()['rows']
    ALL_groups = {}
    group_lvl1 = {}
    group_lvl2 = {}
    for row in rows:
        if row['name'] == 'Astral' and 'Новые товары' in row['pathName']:
            ALL_groups['id_Astral'] = row['id']
        elif row['pathName'] == 'Новые товары/Astral':
            group_lvl1[row['name']] = row['id']
        elif 'Новые товары/Astral/' in row['pathName']:
            group_lvl2[row['name']] = row['id']
    ALL_groups['lvl1'] = group_lvl1
    ALL_groups['lvl2'] = group_lvl2

    # print(ALL_groups)
    return ALL_groups

# Создаем необходимую группу и возвращаем ее id
def create_group(name, id_group):
    data = '{' \
           f'"name": "{name}",' \
           '"productFolder": {' \
           '"meta": {' \
           f'"href": "https://online.moysklad.ru/api/remap/1.2/entity/productfolder/{id_group}",' \
           '"metadataHref": "https://online.moysklad.ru/api/remap/1.2/entity/productfolder/metadata",' \
           '"type": "productfolder",' \
           '"mediaType": "application/json"}}}'.encode('utf-8')
    r = requests.post('https://online.moysklad.ru/api/remap/1.2/entity/productfolder', headers=config.HEADERS_json,
                      data=data)

    return r.json()['id']



# Получаем список всех товаров от поставщика АО Астрал
def get_all_tovar_Astral():
    offset = 0
    stoping = 0

    ALL_tovar = {}

    r_art = requests.get(
        f'https://online.moysklad.ru/api/remap/1.2/entity/product?limit=1000&offset={offset}000',
        headers=config.HEADERS)
    i = 1

    while len(r_art.json()['rows']) != 0:
        rows = r_art.json()['rows']
        for row_art in rows:
            try:
                # if row_art['supplier']['meta']['href'].split('/')[-1] == config.supplier_Astral:
                    # if str(row_art['article']).strip() == '36615':

                id_t = row_art['id']
                buyPrice = row_art['buyPrice']['value']
                # print(row_art)

                rrc = ''
                CTPZ = ''
                prices = row_art['salePrices']
                for price in prices:
                    if price['priceType']['name'] == 'РРЦ Поставщика':
                        rrc = price['value']
                    if price['priceType']['name'] == 'Цена товара под заказ':
                        CTPZ = price['value']
                # print(f'buyPrice - {buyPrice}')
                # print(f'rrc - {rrc}')

                ALL_tovar[str(row_art['article']).strip()] = {
                    'buyPrice': buyPrice,
                    'rrc': rrc,
                    'CTPZ': CTPZ,
                    'id': id_t
                    }
            except:
                pass
            i += 1

        offset += 1
        r_art = requests.get(
            f'https://online.moysklad.ru/api/remap/1.2/entity/product?limit=1000&offset={offset}000',
            headers=config.HEADERS)

    return ALL_tovar

# !!! NEW !!! ALL
# Определяем коэф. умножения цены
def determine_ratio(name):
    s_name = name.split(',')
    ratio = 0

    if len(s_name) == 1:
        ratio = 1

    elif len(s_name) == 2:
        if len(s_name[-1].split('л')) > 1 and s_name[-1].split("л")[0].strip() != 'д':
            ratio = float(s_name[-1].split('л')[0].strip())

        elif len(s_name[-1].split('шт')) > 1:
            if 'в 1 штуке' in s_name[-1]:
                ratio = 1
            else:
                ratio = float(s_name[-1].split('шт')[0].strip().split(' ')[0])

        elif len(s_name[-1].split('кг')) > 1:
            ratio = float(s_name[-1].split('кг')[0].strip())
        else:
            ratio = 1

    elif len(s_name) == 3:
        if len(s_name[-1].split('кг')) > 1 or len(s_name[-2].split('кг')) > 1:
            if 'кг' in s_name[-1]:
                ratio = float(s_name[-1].split('кг')[0].strip())
            else:
                ratio = float(s_name[-2].split('кг')[0].strip())

        elif len(s_name[-1].split(' л')) > 1:
            if s_name[-2].strip() == '0':
                ratio = float(f"0.{s_name[-1].split('л')[0].strip()}")
            else:
                ratio = float(s_name[-1].split('л')[0].strip())
        else:
            ratio = 1

    else:
        if 'кг' in s_name[-1] or 'кг' in s_name[-2]:
            if 'кг' in s_name[-1]:
                ratio = float(f"{s_name[-2].strip()}.{s_name[-1].split('кг')[0].strip()}")

            else:
                ratio = float(s_name[-2].split('кг')[0].strip())
    # print(f'{ratio} - {len(s_name)} - {s_name}')

    return ratio

