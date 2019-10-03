# -*- coding: utf-8 -*-

from django.db import models
from django.db.models import Count
from django.db.models import Q

class ContentManager(models.Manager):
    u"""Менеджер объектов модели Content"""

    def get_pub_mod(self, request, **params):
        u"""Возвращает список опубликованных и прошедших модерацию объектов"""

        is_owner = request.user.is_authenticated() and 'user_id' in params and request.user.id == params['user_id']

        if not request.user.is_staff and not is_owner:
            if self.get_field('moderated'): params.update({'moderated': True})
            if self.get_field('published'): params.update({'published': True})

        objects = self.filter(**params)

        if self.get_field('position'):
            return objects.annotate(null_position=Count('position')).order_by('-null_position', 'position')

        return objects

    def get_field(self, field_name):
        u"""Возвращает поле модели по имени поля"""

        try:
            return self.model._meta.get_field(field_name)
        except:
            try:
                return eval('self.model.' + field_name)
            except:
                return False

class BaseCategoryManager(ContentManager):
    u"""Менеджер объектов модели BaseCategory"""

    def set_tags(self, request=None, css_class='', empty=True):
        u"""
            Метод возвращет все эллементы иерархической модели в иерархической HTML-разметке.
            Используется для построения категорий в поп-апе форм: компании/спикера/мероприятия
        """

        if empty:
            tree = self.model.objects.filter(published=True).order_by('left')
        else:
            tree = self.model.objects.filter(published=True, *[(Q(children__events__isnull=False) | Q(events__isnull=False))]).distinct().order_by('left')

        active, active_left, active_right = None, 0, 0

        if request:
            for i in tree:
                if i.slug == request.path:
                    active, active_left, active_right = i, i.left, i.right
                    break
        else:
            active, active_left, active_right = None, None, None

        level = 1

        css_class = css_class + '-' if css_class else css_class

        for i, item in enumerate(tree):

            item.open, item.close, item.final = '', '', ''
            css_classes = css_class + 'item' # Если хотим использовать MainMenu -> main-menu-item : dasherize(underscore(self.model.__name__) + '-item')

            if item.left + 1 != item.right:
                css_classes += ' parent'
                if item.left < active_left and item.right > active_right:
                    css_classes += ' expanded'
            if item == active:
                css_classes += ' active'
                if item.left + 1 != item.right:
                    css_classes += ' expanded'

            # Открывающий тег есть у всех
            item.open = '<span class="{0} level-{1}">'.format(css_classes, item.level)

            # Если мы первый ребёнок - дополнительно окутываемся
            if item.level > level:
                item.open = '<span class="{0} level-{1}">'.format(css_classes.replace('item', 'block').replace(' parent', ''), item.level) + item.open

            # Если предыдущий был братом - закрываем его
            if item.level == level:
                item.close = '</span>'

            # Если мы упали - смотрим на сколько (level-item.level) помним что все родители имели окна (*2). Не забываем закрыть себя (+1)
            if item.level < level:
                item.close = '</span>' * ((level-item.level) * 2 + 1)

            if i + 1 == len(tree):
                if item.level == 1:
                    item.final = '</span>'
                elif item.level > level:
                    item.final = '</span>' * (item.level*2 - 1)
                elif item.level < level:
                    item.final = '</span>' * ((level-item.level) * 2 + 1)
                elif item.level == level:
                    item.final = '</span>' * (item.level*2 - 1)

            # Если первый раз, то ничего не закрываем
            if i == 0: item.close = ''

            level = item.level

        return tree

    def set_mptt(self, left=1, parent=None, level=1):
        u"""
            Проставляет поля level, left и right всем эллементам иерархической структуры.
            Подробнее в описании core.abs.models.BaseCategory
        """

        models = self.model.objects.filter(parent=parent).order_by('position')
        for i in models:
            data = {
                'level': level,
                'left': left,
                'right': left + (i.count_children() * 2) + 1
            }
            self.model.objects.filter(id=i.id).update(**data)
            left = data['right'] + 1
            self.set_mptt(left=data['left'] + 1, parent=i.id, level=data['level'] + 1)
