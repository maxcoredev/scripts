import re, os
import importlib.util

from django.conf import settings
from django.http import FileResponse

from clients import IEClient, LEClient
from accounts import IEAccount, LEAccount

from docgen.generator import Generator


def data_is_valid(form, post_data, client_type=None):
    """Дополнительная валидация - проверяем наличие указанных объектов в базе"""

    for k, v in post_data.items():
        if k == 'account_new_id':
            if client_type == 'ie':
                if not FLClient.objects.filter(id=v).exists():
                    form.errors.append('Указанный аккаунт не найден')
            elif client_type == 'le':
                if not ULClient.objects.filter(id=v).exists():
                    form.errors.append('Указанный аккаунт не найден')
        # elif some_oth_condition == rule:
        #    pass

    return False if form.errors else True


def get_config(template_name):
    """Функция ищет шаблон по имени и возвращает его конфигурацию: директорию, название, поля, bootstrap col"""

    config, file_name_doc, file_name_py = {}, template_name + '.docx', template_name + '.py'

    for template_dir, dir_names, file_names in os.walk(os.path.join(settings.BASE_DIR, settings.DOC_TEMPLATES_ROOT)):
        if {file_name_doc, file_name_py}.issubset(file_names):

            spec = importlib.util.spec_from_file_location(template_name, os.path.join(template_dir, file_name_py))
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            config['template_dir'] = template_dir
            config['title'] = getattr(mod, 'title', None)
            config['fields'] = getattr(mod, 'form_data', None)
            config['col'] = getattr(mod, 'col', None)

            break

    return config


def get_context(client_type=None, client_id=None, pac_id=None, task=None, client_new_id=None, pac_new_id=None):
    """Описание связей переменных в шаблоне с моделью, эмуляция методов моделей (те самые методы и тот самый маппинг)"""

    # I. Берём объекты из базы

    client, pac, client_new, pac_new = None, None, None, None

    if client_type == 'fl':
        client = FLClient.objects.get(id=client_id) if client_id else FLClient()
        pac = PACFL.objects.get(id=pac_id) if pac_id else PACFL()
        client_new = FLClient.objects.get(id=client_new_id) if client_new_id else FLClient()
        pac_new = PACFL.objects.get(id=pac_new_id) if pac_new_id else PACFL()
    elif client_type == 'ul':
        client = ULClient.objects.get(id=client_id) if client_id else ULClient()
        pac = PACUL.objects.get(id=pac_id) if pac_id else PACUL()
        client_new = ULClient.objects.get(id=client_new_id) if client_new_id else ULClient()
        pac_new = PACUL.objects.get(id=pac_new_id) if pac_new_id else PACUL()

    # II. Формируем контекст, состоящий из Клиента, Аккаунта и глобальных переменных
    # (перекрываем значения объектов в базе значениями из задачи)

    context = {'c': client, 'a': pac, 'cn': client_new, 'an': pac_new}

    if task:
        task_data = task.data.copy()
        for k, v in task_data.items():
            if k.startswith('c.'):
                setattr(context['c'], k.split('.')[1], v)
            elif k.startswith('a.'):
                setattr(context['a'], k.split('.')[1], v)
            else:
                context[k] = v

    # III. Описываем связи переменных в шаблоне с моделью, эмулируем методы (те самые методы и тот самый маппинг)

    for client in ['c', 'cn']:
        context[client].fio = context[client].full_name
        context[client].phone = context[client].full_phone

    for account in ['a', 'an']:
        # context[account].example = context[account].proxy_example
        pass

    return context


def get_pdf_file(template_dir, template_name, context):
    generator = Generator(template_dir, template_name, context)
    return FileResponse(open(generator.document_path_pdf, 'rb'), content_type='application/pdf')
