import django.contrib.postgres.fields
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experts", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="expert",
            name="general_availability",
        ),
        migrations.AddField(
            model_name="expert",
            name="availability_days",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(
                    choices=[
                        ("Monday", "Monday"),
                        ("Tuesday", "Tuesday"),
                        ("Wednesday", "Wednesday"),
                        ("Thursday", "Thursday"),
                        ("Friday", "Friday"),
                        ("Saturday", "Saturday"),
                        ("Sunday", "Sunday"),
                    ],
                    max_length=9,
                ),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="expert",
            name="availability_hours",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.PositiveSmallIntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(23),
                    ]
                ),
                blank=True,
                default=list,
                size=None,
            ),
        ),
    ]
