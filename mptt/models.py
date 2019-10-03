# -*- coding: utf-8 -*-

import json

from collections import OrderedDict

from django.db import models
from django.utils import timezone
from django.utils.text import mark_safe
from django.utils.html import escape
from django.core.cache import cache
from django.conf import settings

from core.abs.managers import ContentManager, BaseCategoryManager


class BaseCategory(models.Model):
    """ Все иерархические объекты должны наследоваться от этого класса.
        Реализуют технику MPTT http://www.sitepoint.com/hierarchical-data-database/
        Используется вместо модуля django-mptt https://github.com/django-mptt/django-mptt/
        Техника MPTT реализуется следующим образом: Каждый раз при сохранении каждого объекта, все объекты переиндексируются
        методом .set_mptt() описанном в менеджере BaseCategoryManager()"""

    title = models.CharField(verbose_name=u'Заголовок', max_length=255)
    slug = models.CharField(verbose_name=u'Ссылка', max_length=255, unique=True)
    left = models.IntegerField(blank=True, null=True)
    right = models.IntegerField(blank=True, null=True)
    parent = models.ForeignKey(verbose_name=u'Родительская категория', to='self', blank=True, null=True, related_name='children')
    position = models.IntegerField(verbose_name=u'Позиция', blank=True, null=True)
    level = models.IntegerField(blank=True, null=True)
    published = models.BooleanField(verbose_name=u'Опубликован', default=True)

    objects = BaseCategoryManager()

    def __unicode__(self):
        level = self.level if self.level else 1
        i = u'| ' if level > 1 else ''
        return unicode(u'|----' * (level - 1)) + unicode(i) + unicode(self.title)

    class Meta:
        ordering = ['left']
        abstract = True

    def save(self, *args, **kwargs):
        super(BaseCategory, self).save(*args, **kwargs)
        type(self).objects.set_mptt()
        cache.clear()

    def count_children(self):
        self.children_count = 0
        def count_them(children):
            for child in children:
                self.children_count += 1
                count_them(child.children.all())
        count_them(self.children.all())
        return self.children_count