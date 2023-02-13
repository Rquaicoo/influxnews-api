# Generated by Django 4.1.5 on 2023-02-13 07:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=2000)),
                ('description', models.TextField()),
                ('url', models.URLField()),
                ('image', models.URLField(default='')),
                ('publishedAt', models.DateTimeField(default=datetime.datetime.now)),
                ('content', models.TextField(default='')),
                ('source', models.CharField(default='', max_length=100)),
                ('category', models.CharField(default='general', max_length=100)),
                ('country', models.CharField(default='worldwide', max_length=100)),
                ('language', models.CharField(default='en', max_length=100)),
                ('date_scraped', models.DateTimeField(auto_now_add=True)),
                ('author', models.CharField(max_length=100)),
            ],
        ),
    ]
