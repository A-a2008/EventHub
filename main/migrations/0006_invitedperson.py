# Generated by Django 4.1.3 on 2023-06-28 15:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_remove_subevents_creators'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvitedPerson',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('event_id', models.IntegerField()),
                ('creator', models.BooleanField()),
                ('subevents', models.CharField(max_length=1000)),
            ],
        ),
    ]