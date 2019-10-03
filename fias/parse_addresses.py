import re
import json

from core.fias import Object, House, Room

CITIES = ('москва', 'санкт-петербург', 'краснодар')

STREET_TYPES = ('ул', 'пр', 'пер', 'пр-т', 'пр-кт', 'б-р', 'ст', 'с/т', 'бул', 'пл', 'парк', 'мкр', 'м', 'х', 'тер', 'п', 'х', 'ш')

with open('addresses.json', encoding='utf-8') as f:
    data = json.load(f)

for record in data['RecordSet']:

    final = {
        'city'         : None,

        'street_type'  : None,
        'street'       : None,

        'house'        : None,
        'corp'         : None,
        'stroen'       : None,

        'room_type'    : None,
        'room'         : None,

        'original'     : record.get('OC_ADDRESS') or ''
    }

    address = final['original'].strip().lower()

    # Вырезаем в начале строки возможный "индекс|г| |.|," (321456 г. батайск -> батайск)
    address = re.sub(r'^(\d|г|\.|,|\s)*', '', address)

    # "батайск[ |.|,]" -> "батайск, "
    for city in CITIES: address = re.sub(r'^{}(\s|,|\.)+'.format(city), city + ', ', address)

    # Приводим в порядок улицу (ул..ленина - такое бывает часто)
    address = address.replace('..', '.')

    # Если адрес пустой - ВАЛИМ
    if not address: continue

    # Если какой либо город встречается дважды - ВАЛИМ во избежании непредвиденных ошибок
    if address.count(CITIES[0]) > 1 or address.count(CITIES[1]) > 1: continue

    # Если встречаются оба города - ВАЛИМ во избежании непредвиденных ошибок
    if address.count(CITIES[0]) >= 1 and address.count(CITIES[1]) >= 1: continue

    # Если адрес начинается не с города (а с области или улицы) - ВАЛИМ (их не много)
    if not address.startswith(CITIES): continue

    # Если есть информация более чем в одних скобках - ВАЛИМ (их не много)
    if address.count('(') > 1 or address.count(')') > 1: continue

    # Если есть только одна какая-то скобка - ВАЛИМ (вроде встречались)
    if address.count('(') > 1 or address.count(')') > 1: continue

    # Если внутри скобок есть "," - заменяем её на ";"
    p = re.search(r'\((.*)\)', address)
    if p: address = address.replace(p.group(), p.group(1).replace(',', ';'))

    # Если нам пришлось вставить разделитель ";" (или он уже где-то был) - ВАЛИМ
    if ';' in address: continue

    # Разбиваем строку, примерно ожидая - город, улица, дом, квартира
    objects = [obj.strip() for obj in address.split(',') if obj.strip()]

    # Нормальный адрес разделяется тремя/четыремя запятыми. Если не так - ВАЛИМ
    if len(objects) not in [3, 4]: continue

    # ЗАПОЛНЯЕМ ГОРОД
    final['city'] = objects[0]

    # ЗАПОЛНЯЕМ ТИП УЛИЦЫ И НАЗВАНИЕ УЛИЦЫ
    for street_type in STREET_TYPES:
        street = re.sub(r'^{}[\.| ]'.format(street_type), '', objects[1]).strip()
        if street != objects[1]:
            final['street_type'] = street_type
            final['street'] = street  # теоретически может содержать номер дома, в этом случае в базе ФИАСа просто ничего не найдётся
            break

    # Если нет типа улицы или названия - ВАЛИМ
    if not final['street_type'] or not final['street']: continue

    # ТРЭШ, КОТОРЫЙ ИДЁТ ПОСЛЕ УЛИЦЫ
    after_street = ' '.join(objects[2:4])

    # Если содержится разделитель "-" - ВАЛИМ
    if '-' in after_street: continue

    # Если встречается и "корп." и "/" - ВАЛИМ (всего один случай вроде)
    if 'корп' in after_street and '/' in after_street: continue

    # Если встречается больше одного "/" - ВАЛИМ
    if address.count('/') > 1: continue

    # Берём всё, что НЕ КВАРТИРА
    house_corp_stroen = re.search(r'(.*)(?=(пом|каб|кв|оф|ком)([\.\s]*)(\W+))', after_street)
    house_corp_stroen = house_corp_stroen.group().strip() if house_corp_stroen else after_street.strip()

    # Вычленяем строение если оно есть
    stroen = re.search(r'стр[\.\s]*(.*)', house_corp_stroen)
    final['stroen'] = stroen.group(1).strip() if stroen else None

    # Далее работаем без строения
    house_corp = house_corp_stroen.split('стр')[0].strip()

    # Вычленяем корпус если он есть
    corp = re.search(r'корп[\.\s]*(.*)', house_corp)
    final['corp'] = corp.group(1).strip() if corp else None

    # Далее работаем без корпуса (буквенного)
    house_corp = house_corp.split('корп')[0].strip().split('/')

    # Забираем ДОМ
    final['house'] = house_corp[0]

    # Если корпус не нашёлся в прошлый раз, но нашёлся сейчас - проставляем
    if len(house_corp) == 2: final['corp'] = house_corp[1]

    # Забираем КОМНАТУ и ТИП КОМНАТЫ
    room = re.search(r'(пом|каб|кв|оф|ком)([\.\s]+)(.+)', after_street)
    final['room_type'] = room.group(1) if room else None
    final['room'] = room.group(3) if room else None

    print(final)