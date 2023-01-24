import requests
import base64
import config
import os
from bs4 import BeautifulSoup as BS4

dir_path = os.path.dirname(os.path.abspath(__file__))

# Проверяем на актульность файлы, если нет в списке, то добавляем в архив
def archive_offer(root):
    Articles = []
    # i = 0
    archive_tovar = 0

    # Собираем список артикулов из актуального файла
    for offer in root.find('shop').find('offers'):

        # Ищем артикул
        params = offer.findall('param')
        for param in params:
            if str(param.get('name')) == 'sku':
                Article = param.text.strip()
                Articles.append(Article)
                break


    # Получаем список товаров с МС
    r = requests.get("https://online.moysklad.ru/api/remap/1.2/entity/product", headers=config.HEADERS)

    r_j = r.json()['rows']

    # Ищем артикулы товаров которые уже добавлены в МС
    for row in r_j:
        # Выбираем необходимую группу
        if 'Новые товары/Акваполис' in row['pathName']:
            # print(2)
            article = row['article']

            # Проверяем, есть ли артикул в актульном списке, если его нет, то помещаем в архив
            if article not in Articles:
                data = '{"archived": true}'.encode('utf-8') #

                # Запрос на поммещенение товара в архив
                rrr = requests.put(f'https://online.moysklad.ru/api/remap/1.2/entity/product/{row["id"]}',
                                   headers=config.HEADERS_json, data=data)

                archive_tovar += 1

    return archive_tovar


# Скачиваем и записываем данные в файл aquapolis.xml
def get_xml_file():
    url = 'https://aquapolis.ru/media/astrio/feed/forpartners_default.yml'

    # Запрос на получение новых данных
    r = requests.get(url)
    data = r.text

    # Запись xml файла
    myfile = open(os.path.join(dir_path, f'aquapolis.xml'), 'w', encoding='utf-8')
    myfile.write(data)


# Формируем данные запроса на основе полученных данных
def create_data_post(tovar, i, id_group):
    if i == '1':
        d = tovar["Description"]
    elif i == '3':
        d = ''
    else:
        d = tovar["Description1"]
    data = '{' \
           f'"article": "{tovar["Article"]}",' \
           f'"name": "{tovar["Name"]}",' \
           f'"description": "{d}",' \
           f'"vat": 20,' \
           '"uom": {' \
           '"meta": {' \
           '"href": "https://online.moysklad.ru/api/remap/1.2/entity/uom/19f1edc0-fc42-4001-94cb-c9ec9c62ec10",' \
           '"metadataHref": "https://online.moysklad.ru/api/remap/1.2/entity/uom/metadata",' \
           '"type": "uom",' \
           '"mediaType": "application/json"}},' \
           '"salePrices": [' \
               '{' \
               f'"value": {round(float(tovar["minPrice"]), 2) * 100},' \
               '"priceType": {' \
               '"meta": {' \
               f'"href": "https://online.moysklad.ru/api/remap/1.2/context/companysettings/pricetype/{config.RRC_POST}",' \
               '"type": "pricetype",' \
               '"mediaType": "application/json"' \
               '}}},' \
           '{' \
           f'"value": {round(float(tovar["priseSale"]), 2) * 100},' \
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
           f'"href": "https://online.moysklad.ru/api/remap/1.2/entity/supplier/{config.supplier_Akvapolis}",' \
           '"metadataHref": "https://online.moysklad.ru/api/remap/1.2/entity/counterparty/metadata",' \
           '"type": "counterparty",' \
           '"mediaType": "application/json"}},' \
           f'"images": {str(tovar["IMG"])}' \
           '}'#.encode('utf-8')
    # print(data)
    return data


# Формируем данные запроса на основе полученных данных для обновления
def create_data_put(row_dict):
    data = '{' \
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


# Формируем словарь данных для отправки в базу МС
def form_dict_data(offer):
    name = offer.find('name').text.strip()  # Получаем  название товара
    price = offer.find('price').text.strip()    # Получаем цену товара
    # print(price)

    # Ищем артикул
    params = offer.findall('param')
    for param in params:
        if str(param.get('name')) == 'sku':
            Article = param.text.strip()
            break

    # Ищем изобращение
    pictures = offer.findall('picture')
    IMGS = []
    for picture in pictures[::-1]:
        IMGS.append(picture.text.strip())
    # print(f"IMGS - {IMGS}\n{len(IMGS)}")

    # Формируем описание товара
    description = ''
    descriptions = offer.find('description')
    try:
        description += descriptions.text.strip()
    except:
        pass
    if len(description) == 0:
        descriptions = offer.findall('param')
        for param in descriptions:
            if str(param.get('name')) == 'dopolnitelno':
                description += param.text.strip().replace('"', "'")  # .replace('\n', ' ')
                break

    # Объявляем словарь данных
    row_dict = {}


    row_dict['Article'] = Article
    row_dict['Name'] = name.replace('"', "'").replace('\\', ' ')
    # row_dict['buyPrice'] = row[4]
    row_dict['minPrice'] = price
    row_dict['priseSale'] = float(row_dict['minPrice']) * 1.1  # !!! NEW !!!

    # Обрабатываем описание товара, чтобы прошел проверку под требования МС
    row_dict['Description'] = description.split('<style>')[0].replace("\n", "").replace('"', "'").replace('\t', '').replace(
        '<!-- Графики СПА бассейна -->', '') \
        .replace('<!-- \\ -->', '').replace('<!-- / -->', '').replace('<!-- // -->', '').replace('<!-- /// -->', '') \
        .replace('<!-- Общий блок -->', '').replace('<!-- Блок на 50% -->', '').replace(
        '<!-- Универсальный текст -->', '') \
        .replace('<!-- \ -->', '').replace('<!-- \\ -->', '').replace('<!-- \\\ -->', '').replace('<!-- \\\\ -->',
                                                                                                  '') \
        .replace('<!-- \\\\\ -->', '').replace('<!-- \\\\\\ -->', '').replace('<!-- \\\\ -->', '').replace(
        '<!-- \\\\ -->', ''). \
        replace('℃', 'C').replace('"', "'").replace('<!--Блок на всю ширину экрана для начинки-->', ''). \
        replace('<!--Текстовый блок--> ', '').replace('<!--/--> ', '').replace('<!--//--> ', '').replace(
        '<!--///--> ', ''). \
        replace('<!--////--> ', '').replace('<!--/////--> ', '').replace('<!--//////--> ', '').replace('<!--\\-->',
                                                                                                       ''). \
        replace('<!--\-->', '').replace('<!--\\\-->', '').replace('<!--\\\\-->', '').replace('<!--\\\\\-->', ''). \
        replace('<!--\\\\\\-->', '').replace('<!-- / -->', '').replace('<!-- / -->', '').replace('\\\\', ' '). \
        replace('<!-- Top Block -->', '').replace('<!-- END [Top Block] -->', '').replace('\\', ' ')


    try:
        soup = BS4(description, 'lxml')
        row_dict['Description1'] = soup.text.strip().replace('\n', ' ').replace('  ', ' ')
    except:
        row_dict['Description1'] = ''

    images = {}
    I = []
    img_dict = {'filename': '',
                'content': ''}
    n_img = 1
    for IMG in IMGS:
        img_dict = {}
        # Получаем изоображение товара
        img_r = requests.get(IMG)
        img_dict['filename'] = f'{row_dict["Article"]}_{n_img}'
        img_dict['content'] = str(base64.b64encode(img_r.content)).split("'")[1].split("'")[0]
        I.append(img_dict)
        n_img += 1
    row_dict['IMG'] = str(I).replace("'", '"')


    return row_dict

# Получаем список сохраненных id групп
def get_all_groups():
    r = requests.get('https://online.moysklad.ru/api/remap/1.2/entity/productfolder', headers=config.HEADERS)
    # print(r.text)
    rows = r.json()['rows']
    ALL_groups = {}
    group_lvl1 = {}
    group_lvl2 = {}
    group_lvl3 = {}
    for row in rows:
        if row['name'] == 'Акваполис' and 'Новые товары' in row['pathName']:
            ALL_groups['id_Aquapolis'] = row['id']
        elif row['pathName'] == 'Новые товары/Акваполис':
            group_lvl1[row['name']] = row['id']
        # elif 'Новые товары/Акваполис/' in row['pathName']:
        elif 'Акваполис' in row['pathName'] and len(row['pathName'].split('/')) == 3:
            group_lvl2[row['name']] = row['id']
        elif 'Акваполис' in row['pathName'] and len(row['pathName'].split('/')) == 4:
            group_lvl3[row['name']] = row['id']
    ALL_groups['lvl1'] = group_lvl1
    ALL_groups['lvl2'] = group_lvl2
    ALL_groups['lvl3'] = group_lvl3

    # print(ALL_groups)
    return ALL_groups


# Создаем карту категорий из файла
def maps_categories(root):
    dir_path = os.path.dirname(os.path.abspath(__file__))

    ALL_categories = {}

    for offer in root.find('shop').find('categories'):
        # print(f"{offer.get('id')} - {offer.get('parentId')} - {offer.text.strip()}")

        id_cat = offer.get('id')
        parentId = offer.get('parentId')
        name_cat = offer.text.strip()

        if id_cat not in ALL_categories and parentId == None:
            ALL_categories[id_cat] = {
                'name': name_cat,
                'parentId': {}
            }
            continue

        if id_cat not in ALL_categories and parentId != None and parentId in ALL_categories:
            ALL_categories[parentId]['parentId'][id_cat] = {
                'name': name_cat,
                'parentId': {}
            }

        if id_cat not in ALL_categories and parentId != None and parentId not in ALL_categories:
            for key_1 in ALL_categories:
                # print(key_1)
                for key_2 in ALL_categories[key_1]['parentId']:
                    # print(key_2)
                    if parentId == key_2:
                        n = ALL_categories[key_1]['parentId'][key_2]['name']

                        ALL_categories[key_1]['parentId'][key_2]['parentId'][id_cat] = name_cat
                        break

    # print(ALL_categories)
    return ALL_categories

# Создаем путь до нужной категории
def create_path_categories(cat_ids, ALL_categories):
    if str(cat_ids) in ALL_categories:
        # print(1)
        # print(ALL_categories[str(cat_ids)])
        # path_cat = f'path_cat >>> {cat_ids} = {ALL_categories[str(cat_ids)]["name"]}'
        path_cat = {
            'lvl1': {
                'id': cat_ids,
                'name': ALL_categories[str(cat_ids)]["name"]
            }
        }
        # print(path_cat)
    else:
        for lvl1 in ALL_categories:
            if str(cat_ids) in ALL_categories[lvl1]['parentId']:
                path_cat = {
                    'lvl1': {
                        'id': lvl1,
                        'name': ALL_categories[lvl1]["name"]
                    },
                    'lvl2': {
                        'id': cat_ids,
                        'name': ALL_categories[lvl1]["parentId"][str(cat_ids)]["name"]
                    }
                }
            else:
                for lvl2 in ALL_categories[lvl1]['parentId']:
                    if str(cat_ids) in ALL_categories[lvl1]['parentId'][lvl2]['parentId']:
                        path_cat = {
                            'lvl1': {
                                'id': lvl1,
                                'name': ALL_categories[lvl1]["name"]
                            },
                            'lvl2': {
                                'id': lvl2,
                                'name': ALL_categories[lvl1]["parentId"][lvl2]["name"]
                            },
                            'lvl3': {
                                'id': cat_ids,
                                'name': ALL_categories[lvl1]["parentId"][lvl2]["parentId"][str(cat_ids)]
                            }
                        }

    # print(len(path_cat))
    return path_cat

# Создаем нужную группу, которой не было
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
def get_all_tovar_aquapolis():
    offset = 0
    ALL_tovar = {}
    r_art = requests.get(
        f'https://online.moysklad.ru/api/remap/1.2/entity/product?limit=1000&offset={offset}000',
        headers=config.HEADERS)
    i = 1

    while len(r_art.json()['rows']) != 0:
        rows = r_art.json()['rows']
        for row_art in rows:
            # print(row_art)
            try:
                id_t = row_art['id']

                rrc = ''
                CTPZ = ''
                prices = row_art['salePrices']
                for price in prices:
                    if price['priceType']['name'] == 'РРЦ Поставщика':
                        rrc = price['value']
                    if price['priceType']['name'] == 'Цена товара под заказ':
                        CTPZ = price['value']

                ALL_tovar[str(row_art['article']).strip()] = {
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

