# Generated by Django 3.2.3 on 2021-06-29 13:29

import desecapi.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('desecapi', '0016_default_auto_field'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='limit_domains',
            field=models.PositiveIntegerField(blank=True, default=desecapi.models.User._limit_domains_default, null=True),
        ),
    ]
