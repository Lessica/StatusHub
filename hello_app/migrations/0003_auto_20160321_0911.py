# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-03-21 09:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('hello_app', '0002_auto_20160321_0846'),
    ]

    operations = [
        migrations.RenameField(
            model_name='respdatamodel',
            old_name='contents',
            new_name='response_body',
        ),
        migrations.RenameField(
            model_name='respdatamodel',
            old_name='header',
            new_name='response_header',
        ),
        migrations.RemoveField(
            model_name='respdatamodel',
            name='size',
        ),
    ]
