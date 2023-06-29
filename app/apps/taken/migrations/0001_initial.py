# Generated by Django 3.2.16 on 2023-06-28 10:40

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("aliassen", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Taak",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("aangemaakt_op", models.DateTimeField(auto_now_add=True)),
                ("aangepast_op", models.DateTimeField(auto_now=True)),
                ("afgesloten_op", models.DateTimeField(blank=True, null=True)),
                ("taakopdracht", models.URLField()),
                (
                    "resolutie",
                    models.CharField(
                        choices=[
                            ("opgelost", "Opgelost"),
                            ("niet_opgelost", "Niet opgelost"),
                        ],
                        default="niet_opgelost",
                        max_length=50,
                    ),
                ),
                ("titel", models.CharField(max_length=100)),
                ("bericht", models.CharField(blank=True, max_length=500, null=True)),
                ("additionele_informatie", models.JSONField(default=dict)),
                (
                    "melding",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="taken_voor_meldingalias",
                        to="aliassen.meldingalias",
                    ),
                ),
            ],
            options={
                "verbose_name": "Taak",
                "verbose_name_plural": "Taken",
                "ordering": ("-aangemaakt_op",),
            },
        ),
        migrations.CreateModel(
            name="Taaktype",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("aangemaakt_op", models.DateTimeField(auto_now_add=True)),
                ("aangepast_op", models.DateTimeField(auto_now=True)),
                ("omschrijving", models.CharField(max_length=200)),
                (
                    "toelichting",
                    models.CharField(blank=True, max_length=500, null=True),
                ),
                ("additionele_informatie", models.JSONField(default=dict)),
            ],
            options={
                "verbose_name": "Taaktype",
                "verbose_name_plural": "Taaktypes",
                "ordering": ("-aangemaakt_op",),
            },
        ),
        migrations.CreateModel(
            name="Taakstatus",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("aangemaakt_op", models.DateTimeField(auto_now_add=True)),
                ("aangepast_op", models.DateTimeField(auto_now=True)),
                (
                    "naam",
                    models.CharField(
                        choices=[
                            ("nieuw", "Nieuw"),
                            ("bezig", "Bezig"),
                            ("voltooid", "Voltooid"),
                        ],
                        default="nieuw",
                        max_length=50,
                    ),
                ),
                (
                    "taak",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="taakstatussen_voor_taak",
                        to="taken.taak",
                    ),
                ),
            ],
            options={
                "verbose_name": "Taakstatus",
                "verbose_name_plural": "Taakstatussen",
                "ordering": ("-aangemaakt_op",),
            },
        ),
        migrations.CreateModel(
            name="Taakgebeurtenis",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "uuid",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("aangemaakt_op", models.DateTimeField(auto_now_add=True)),
                ("aangepast_op", models.DateTimeField(auto_now=True)),
                (
                    "omschrijving_intern",
                    models.CharField(blank=True, max_length=5000, null=True),
                ),
                ("gebruiker", models.CharField(blank=True, max_length=200, null=True)),
                (
                    "taak",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="taakgebeurtenissen_voor_taak",
                        to="taken.taak",
                    ),
                ),
                (
                    "taakstatus",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="taakgebeurtenis_voor_taakstatus",
                        to="taken.taakstatus",
                    ),
                ),
            ],
            options={
                "verbose_name": "Taakgebeurtenis",
                "verbose_name_plural": "Taakgebeurtenissen",
                "ordering": ("-aangemaakt_op",),
            },
        ),
        migrations.AddField(
            model_name="taak",
            name="taakstatus",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="taak_voor_taakstatus",
                to="taken.taakstatus",
            ),
        ),
        migrations.AddField(
            model_name="taak",
            name="taaktype",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="taken_voor_taaktype",
                to="taken.taaktype",
            ),
        ),
    ]
