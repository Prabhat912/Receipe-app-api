# Generated by Django 3.2.25 on 2024-04-04 17:03

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20230926_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='receipe',
            name='image',
            field=models.ImageField(null=True, upload_to=core.models.receipe_image_file_path),
        ),
    ]
