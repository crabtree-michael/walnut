import uuid
from django.db import migrations, models
import django.db.models.deletion
import django.contrib.postgres.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Expert",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("photo", models.URLField(blank=True)),
                (
                    "expertise",
                    models.CharField(
                        choices=[("Personal Trainer", "Personal Trainer")],
                        max_length=64,
                    ),
                ),
                (
                    "specialities",
                    django.contrib.postgres.fields.ArrayField(
                        base_field=models.CharField(
                            choices=[
                                ("Strength & Conditioning", "Strength & Conditioning"),
                                ("Functional Fitness", "Functional Fitness"),
                                (
                                    "High-Intensity Interval Training (HIIT)",
                                    "High-Intensity Interval Training (HIIT)",
                                ),
                                (
                                    "Endurance Training (marathon, triathlon prep)",
                                    "Endurance Training (marathon, triathlon prep)",
                                ),
                                ("Speed & Agility Training", "Speed & Agility Training"),
                                (
                                    "Corrective Exercise / Postural Alignment",
                                    "Corrective Exercise / Postural Alignment",
                                ),
                                ("Population-Specific Training", "Population-Specific Training"),
                                ("Youth Fitness", "Youth Fitness"),
                                ("Senior Fitness", "Senior Fitness"),
                                (
                                    "Pre-natal & Post-natal Training",
                                    "Pre-natal & Post-natal Training",
                                ),
                                ("Adaptive Fitness", "Adaptive Fitness"),
                                ("Chronic Conditions", "Chronic Conditions"),
                                (
                                    "Post-Rehabilitation / Injury Recovery",
                                    "Post-Rehabilitation / Injury Recovery",
                                ),
                                ("Athletic & Sport-Specific", "Athletic & Sport-Specific"),
                                ("Sports Performance Coaching", "Sports Performance Coaching"),
                                ("Powerlifting Coaching", "Powerlifting Coaching"),
                                ("Olympic Weightlifting", "Olympic Weightlifting"),
                                ("CrossFit Specialty Coaching", "CrossFit Specialty Coaching"),
                                ("Combat Sports Conditioning", "Combat Sports Conditioning"),
                                (
                                    "Running & Endurance Coaching",
                                    "Running & Endurance Coaching",
                                ),
                                (
                                    "Health & Wellness Integration",
                                    "Health & Wellness Integration",
                                ),
                                (
                                    "Weight Loss / Fat Loss Programs",
                                    "Weight Loss / Fat Loss Programs",
                                ),
                                ("Muscle Hypertrophy", "Muscle Hypertrophy"),
                                ("Nutrition Coaching", "Nutrition Coaching"),
                                (
                                    "Stress Management & Mind-Body Training",
                                    "Stress Management & Mind-Body Training",
                                ),
                                ("Holistic Fitness", "Holistic Fitness"),
                                ("Niche & Lifestyle-Oriented", "Niche & Lifestyle-Oriented"),
                                (
                                    "Online / Virtual Fitness Coaching",
                                    "Online / Virtual Fitness Coaching",
                                ),
                                ("Outdoor / Adventure Training", "Outdoor / Adventure Training"),
                                ("Workplace / Corporate Wellness", "Workplace / Corporate Wellness"),
                                ("Group Fitness Leadership", "Group Fitness Leadership"),
                                ("Military / Tactical Fitness", "Military / Tactical Fitness"),
                            ],
                            max_length=128,
                        ),
                        default=list,
                        size=None,
                    ),
                ),
                ("general_availability", models.TextField(blank=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Client",
            fields=[
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
                ("name", models.CharField(max_length=255)),
                ("photo", models.CharField(blank=True, max_length=255)),
                ("birthdate", models.DateField(blank=True, null=True)),
                ("objective", models.TextField()),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("time", models.DateTimeField()),
                (
                    "client",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointments",
                        to="experts.client",
                    ),
                ),
                (
                    "expert",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="appointments",
                        to="experts.expert",
                    ),
                ),
            ],
            options={"ordering": ["time"]},
        ),
    ]
