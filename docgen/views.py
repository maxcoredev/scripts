import re, os

from urllib.parse import urlencode

from django.shortcuts import render, reverse, redirect

from fw import Page, Form, Control

from tasks import Task
from clients import IEClient, LEClient
from accounts import IEAccount, LEAccount

from docgen.utils import get_config, get_context, get_pdf_file, data_is_valid
from docgen.generator import Generator
from docgen.constants import FORM_FIELDS, FORM_LISTS


def create(request, template_name=None, client_type=None, object_type=None, object_id=None):

    # I. Вытягиваем ID Клиента и Аккаунта откуда это возможно и формируем form action,
    #    замыкая обработку формы на эту же view
    post_data, task_data = request.POST.copy(), {}
    Client, client_id, client, Account, account_id, account = None, None, None, None, None, None

    if object_type != 'task':

        # Если задачи ещё нет - вытягиваем id объектов на основе url параметров

        if object_type == 'client':
            client_id = object_id
            slug = 'ie_client' if client_type == 'ie' else 'le_client'
            form_action = reverse('gui:docgen:create_' + slug, args=[template_name, object_id])
        elif object_type == 'account':
            account_id = object_id
            slug = 'ie_account' if client_type == 'ie' else 'le_account'
            form_action = reverse('gui:docgen:create_' + slug, args=[template_name, object_id])
        else:
            form_action = reverse('gui:docgen:create_' + client_type, args=[template_name])

        button_text = 'Создать документ'

    else:

        # Если задача есть - вытягиваем ID объектов из её data

        task = Task.objects.get(id=object_id)
        task_data = task.data

        template_name = task_data['meta']['template_name']
        client_type = task_data['meta']['client_type']
        client_id = task_data['meta']['client_id']
        account_id = task_data['meta']['account_id']

        form_action = reverse('gui:docgen:create_task', args=[object_id])
        button_text = 'Сохранить изменения'

    # II. Получаем объекты Клиента и ЛС

    if client_type == 'ie':
        Client = IEClient
        if object_type == 'account':
            acount = IEAccount
    elif client_type == 'le':
        Client = LEClient
        if object_type == 'account':
            account = LEAccount

    account = Account.objects.get(id=account_id) if account_id else None
    client = Client.objects.get(id=client_id) if client_id else None
    client = account.client if not client and account else client

    # III. По template_name находим необходимый шаблон и достаём из него заголовок, конфигурацию формы и ширину колонок

    config = get_config(template_name)

    # IV. Конструируем page, breadcrumbs и area
    page = Page(user=request.user, title=config['title'], navigation=construct_mainnav())

    page.add_breadcrumb('Документы', reverse('gui:dashboard'))
    if client:
        page.add_breadcrumb(client.full_name, reverse('gui:{}:client_detail'.format(client_type), args=[client.id]))
    if account:
        page.add_breadcrumb(account.title, reverse('gui:{}:account_detail'.format(client_type), args=[account.id]))
    page.add_breadcrumb(config['title'])

    page.add_areas(['zone'])
    zone = page.area('zone')

    if object_type == 'task':
        # Если есть задача - добавляем кнопки для перехода в задачу и документ
        controls = zone.add_controls(name='controls', data=Control())
        controls.add_btn(title='Открыть документ', color='primary',
                         url=reverse('gui:docgen:open_task', args=[object_id]), target='_blank')
        controls.add_btn(title='Перейти к задаче', color='primary',
                         url=reverse('gui:tasks:show', args=[object_id]))

    # V. Создаём форму и конструируем поля

    form = zone.add_form(name='form', data=Form(name='create', css_class='needs-validation',
                                                     novalidate=True, action=form_action))
    form.add_button(title=button_text, status='primary', submit=True)

    for field in config['fields']:

        name = field.get('name')
        field_name = name.split('.')[-1]

        # 1) Ищем значение для value
        value = None
        # Пробуем взять значение из модели
        if object_type in ['client', 'account']:
            if name.startswith('c.'):
                value = getattr(client, field_name)
            elif name.startswith('a.'):
                value = getattr(account, field_name)
        # Пробуем взять значение из задачи
        if task_data and task_data.get(name):
            value = task_data.get(name)
        # Пробуем взять значение из поста
        if post_data:
            flat_value = post_data.get(name)
            list_value = post_data.getlist(name + '[]')
            post_data_value = flat_value or list_value
            value = post_data_value

        # 2) Собираем параметры для генерации виджета
        params = {
            'name'     : field['name'],
            'title'    : field['title'],
            'value'    : value,
            'help_text': field.get('help_text'),
            'css_class': field.get('col') or config['col'] or 'col-6',
            'required' : True
        }

        # 3) Ищем значение для field_type
        field_type = None
        for k, v in FORM_FIELDS.items():
            if name in v:
                field_type = k
                break
        if field_type:
            params['field'] = field_type

        # 4) Расширяем параметры для некоторых виджетов
        if field_type == 'checkgrid':
            params['field'] = 'checkgrid'
            params['data'] = FORM_LISTS.get(name)
        elif field_type == 'phone':
            params['country'] = post_data.get(field['name'] + '_country') or task_data.get(field['name'] + '_country')

        # 5) Передаём кодексу для построения html-элемента
        form.add_field(**params)

    # VI. Обрабатываем POST
    if request.method == 'POST'\
        and form.is_valid()\
        and data_is_valid(form=form, post_data=post_data, client_type=client_type):

        # Пересобираем данные из POST для записи в JSON поле Task.data
        post_data.pop('csrfmiddlewaretoken')
        for k in post_data.keys():
            if '[]' in k:
                post_data[k.replace('[]', '')] = post_data.getlist(k)
                post_data.pop(k)
        post_data = post_data.dict()

        if object_type != 'task':

            # Создаём таск, дополняем post_data словарём "meta"

            post_data['meta'] = {}
            post_data['meta']['client_type'] = client_type
            post_data['meta']['template_name'] = template_name
            if client: post_data['meta']['client_id'] = client.id
            if account: post_data['meta']['account_id'] = account.id

            new_task = Task.first_step(template_name, new_data=post_data)

            # Если для этого шаблона нет задача - отправляем документ на открытие, добавляя GET-параметры
            if not new_task:
                get_params = urlencode({**post_data, **post_data.pop('meta')})
                return redirect('{}?{}'.format(reverse('gui:docgen:open'), get_params))

            # Если задача есть - записываем id для финального редиректа
            else:
                task_id = new_task.id
        else:

            # Обновляем таск
            task_id = object_id
            task = Task.objects.get(id=task_id)
            post_data['meta'] = task.data['meta']
            task.data = post_data
            task.save()

        # В любом случае - переходим к таску
        return redirect(reverse('gui:docgen:create_task', args=[task_id]))

    return render(request, 'admin_page.html', {'page': page})


def open(request, task_id=None):

    # I. Берём конфиг из таска

    task = Task.objects.get(id=task_id) if task_id else None

    template_name = task.data['meta']['template_name'] if task_id else request.GET.get('template_name')
    client_type = task.data['meta']['client_type'] if task_id else request.GET.get('client_type')
    client_id = task.data['meta'].get('client_id') if task_id else request.GET.get('client_id')
    account_id = task.data['meta'].get('account_id') if task_id else request.GET.get('account_id')
    client_new_id = request.GET.get('client_new_id')
    account_new_id = request.GET.get('account_new_id')

    # II. Формируем контекст

    context = get_context(client_type=client_type, client_id=client_id, account_id=account_id, task=task,
                          client_new_id=client_new_id, account_new_id=account_new_id)

    # III. Генерируем PDF-документ из docx-шаблона

    return get_pdf_file(get_config(template_name)['template_dir'], template_name, context)


def generate(request, template_name=None, client_type=None, client_id=None, account_id=None):
    
    # I. Берём конфиг
    
    config = get_config(template_name)

    # II. Формируем контекст

    context = get_context(client_type=client_type, client_id=client_id, account_id=account_id)

    # III. Генерируем PDF-документ из docx-шаблона

    return get_pdf_file(config['template_dir'], template_name, context)
