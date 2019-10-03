import os, re, requests, patoolib

import xml.etree.cElementTree as ET

from xml.etree import ElementTree

from time import time, gmtime, strftime

from collections import OrderedDict

from django.conf import settings
from django.core.management import BaseCommand

from fias.models import (OperationStatus, NormativeDocumentType, NormativeDocument,
                         ActualStatus, AddressObjectType, CenterStatus, CurrentStatus,
                         Object, EstateStatus, StructureStatus, HouseStateStatus, House,
                         FlatType, RoomType, Room, Stead)


class Command(BaseCommand):
    """
    Команда для загрузки ФИАС в базу данных - дельту, или отдельный документ по его имени

    I. Для загрузки отдельного документа, нужно вызвать команду, передав часть имени файла, описанных в поле models:

    python manage.py load_fias --file OPERSTAT

    - Полезно при первичной загрузке основной базы ФИАС отдельными файлами
    - Загружать документы следует по порядку, описанном в поле models
    - Документы должны быть размещены по пути, указанном в setting.FIAS_DIR

    II. Для загрузки новых дельт (относительно последней загрузки) нужно вызвать команду без параметров:

    python manage.py load_fias

    - Метод должен вызываться по cron-у / celery раз в неделю (по рекомендацуии разработчиков API ФИАС)
    - Документы будут загружены в os.path.join(setting.FIAS_DIR, last_loaded_version)  # /www/project/fias/574/

    """

    help = 'Команда для загрузки ФИАС в базу данных - дельту, или отдельный документ по его имени'

    models = OrderedDict([

        ['OPERSTAT', OperationStatus],

        ['NDOCTYPE', NormativeDocumentType],
        ['NORMDOC', NormativeDocument],

        ['ACTSTAT', ActualStatus],
        ['SOCRBASE', AddressObjectType],
        ['CENTERST', CenterStatus],
        ['CURENTST', CurrentStatus],
        ['ADDROBJ', Object],

        ['ESTSTAT', EstateStatus],
        ['STRSTAT', StructureStatus],

        ['HSTSTAT', HouseStateStatus],
        ['HOUSE', House],

        ['FLATTYPE', FlatType],
        ['ROOMTYPE', RoomType],
        ['ROOM', Room],

        ['STEAD', Stead]

    ])

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str)

    def handle(self, *args, **options):

        file = options.get('file')

        # Если указан файл - загружаем файл
        if file:
            self.load_to_db(file=file)

        # Иначе - дельту
        else:
            self.download_delta()

    def download_delta(self):
        """ Функция последовательно:
            1) Проверяет наличие новых дельт,
            2) Скачивает архивы дельт
            3) Распаковывает архивы, получая XML для каждой из таблиц
            4) Вызывает функцию загрузки каждого из файлов"""

        # I. Запрашиваем информацию о последних дельтах
        # Подробнее на: https://fias.nalog.ru/WebServices/Public/DownloadService.asmx?op=GetLastDownloadFileInfo

        envelope = """<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
          <soap:Body>
            <GetAllDownloadFileInfo xmlns="https://fias.nalog.ru/WebServices/Public/DownloadService.asmx" />
          </soap:Body>
        </soap:Envelope>""".encode('utf-8')

        headers = {'Host': 'fias.nalog.ru', 'Content-Type': 'text/xml; charset=utf-8', 'Content-Length': str(len(envelope))}

        response = requests.post(url='https://fias.nalog.ru/WebServices/Public/DownloadService.asmx', headers=headers, data=envelope)

        tree = ElementTree.fromstring(response.content)

        ns = {'ns': 'https://fias.nalog.ru/WebServices/Public/DownloadService.asmx'}

        # II. Получаем последнюю загруженную версию дельты

        current_version = 574  # TODO: current_version брать из базы

        # III. Итерируемся по каждой записи из списка дельт

        for el in tree.findall('.//ns:DownloadFileInfo', ns):

            version = int(el.find('.//ns:VersionId', ns).text)
            delta = el.find('.//ns:FiasDeltaXmlUrl', ns).text
            file_name = 'fias_delta_xml.rar'

            # Если версия дельты больше загруженной:
            if version > int(current_version):

                current_version = str(version)  # TODO: current_version записывать в базу

                # 1) Скачиваем и сохраняем архив с XML-файлами
                response = requests.get(delta)
                rar = os.path.join(settings.FIAS_DIR, current_version, file_name)

                os.makedirs(os.path.dirname(rar), exist_ok=True)
                with open(rar, 'wb') as f:
                    f.write(response.content)

                # 2) Распаковываем архив
                patoolib.extract_archive(rar, outdir=os.path.join(settings.FIAS_DIR, current_version), interactive=False)

                # 3) Вызываем функцию загрузки для каждого из файлов
                for file in self.models.keys():
                    self.load_to_db(file=file, delta=current_version)


    def load_to_db(self, file, delta=None):
        """Функция загружает XML-файл в соответствующую таблицу"""

        # I. Устанавливаем переменные

        # Берём Django-модель по имени файла
        model = self.models[file]

        # Переменные для логирования и замеров времени
        start, ten_minutes, objects_completed, row_index = time(), 0, 0, 0

        # Если функция вызвана для загрузки дельты, переходим в папку с соответствующей версией
        fias_dir = os.path.join(settings.FIAS_DIR, delta) if delta else settings.FIAS_DIR

        # Так как имя XML-файла похоже на:
        # AS_OPERSTAT_20190815_8aeaf9b6-31e3-4059-b098-654a64b355e3.XML
        # Ищем его по имеющемуся имени модели (Пример: OPERSTAT)
        path = None
        for name in os.listdir(fias_dir):
            if re.match('AS_' + file + '_\S*\.XML', name):
                path = os.path.join(fias_dir, name)
        if not path:
            raise Exception('There is no document with name ' + file)

        # II. Итерируемся по каждой записи в XML

        context = iter(ET.iterparse(path, events=('start', 'end')))
        _, root = next(context)  # get root element

        for event, el in context:

            now = strftime("%d.%m.%Y %H:%M:%S", gmtime())

            if event == 'end' and el.tag == model.__name__:

                # Считаем итерации и выводим сообщение каждые миллион записей
                row_index += 1
                if not row_index % 1000000:
                    print(now, row_index)

                # Берём атрибуты, описанные в XML
                attrs = {k.lower(): v for k, v in el.attrib.items()}

                # Собираем параметры для создания Django-объекта
                params = {}
                for k, v in attrs.items():
                    if k == 'flattype': k = 'flattypeid'
                    if k == 'rmtype': k = 'roomtype'
                    if k == 'normdoc': k = 'normdocid'
                    if model._meta.get_field(k).get_internal_type() == 'ForeignKey':
                        params[k + '_id'] = v
                    else:
                        params[k] = v

                try:
                    # Если загружаемый объект существует: пишем сообщение
                    if model.objects.filter(pk=params[model._meta.pk.name]).exists():
                        print(now, model._meta.pk.name, 'with', params[model._meta.pk.name], 'already exists')
                    # Если не существует - создаём
                    else:
                        model.objects.create(**params)
                except Exception as e:
                    print(now, 'VERY UNEXPECTED ERROR', e)

                root.clear()

            # Выводим информацию о кол-ве загруженных документов каждые 10 минут
            objects_completed += 1
            if time() - start - ten_minutes >= 600:
                ten_minutes += 600
                in_minutes = ten_minutes / 60
                print(now, f'{in_minutes} minutes passed, {objects_completed} completed')

        # Выводим информацию о том сколько всего и за какое время загружено
        print('Completed for', (time() - start) / 60, 'minutes.', 'Inserted:', row_index)
