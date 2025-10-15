import uuid

from django.contrib.postgres.fields import ArrayField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Expertise(models.TextChoices):
    PERSONAL_TRAINER = "Personal Trainer", "Personal Trainer"


class Speciality(models.TextChoices):
    STRENGTH_CONDITIONING = "Strength & Conditioning", "Strength & Conditioning"
    FUNCTIONAL_FITNESS = "Functional Fitness", "Functional Fitness"
    HIIT = "High-Intensity Interval Training (HIIT)", "High-Intensity Interval Training (HIIT)"
    ENDURANCE_TRAINING = "Endurance Training (marathon, triathlon prep)", "Endurance Training (marathon, triathlon prep)"
    SPEED_AGILITY = "Speed & Agility Training", "Speed & Agility Training"
    CORRECTIVE_EXERCISE = "Corrective Exercise / Postural Alignment", "Corrective Exercise / Postural Alignment"
    POPULATION_SPECIFIC = "Population-Specific Training", "Population-Specific Training"
    YOUTH_FITNESS = "Youth Fitness", "Youth Fitness"
    SENIOR_FITNESS = "Senior Fitness", "Senior Fitness"
    PRENATAL_POSTNATAL = "Pre-natal & Post-natal Training", "Pre-natal & Post-natal Training"
    ADAPTIVE_FITNESS = "Adaptive Fitness", "Adaptive Fitness"
    CHRONIC_CONDITIONS = "Chronic Conditions", "Chronic Conditions"
    POST_REHABILITATION = "Post-Rehabilitation / Injury Recovery", "Post-Rehabilitation / Injury Recovery"
    ATHLETIC_SPORT_SPECIFIC = "Athletic & Sport-Specific", "Athletic & Sport-Specific"
    SPORTS_PERFORMANCE = "Sports Performance Coaching", "Sports Performance Coaching"
    POWERLIFTING = "Powerlifting Coaching", "Powerlifting Coaching"
    OLYMPIC_WEIGHTLIFTING = "Olympic Weightlifting", "Olympic Weightlifting"
    CROSSFIT_SPECIALTY = "CrossFit Specialty Coaching", "CrossFit Specialty Coaching"
    COMBAT_SPORTS = "Combat Sports Conditioning", "Combat Sports Conditioning"
    RUNNING_ENDURANCE = "Running & Endurance Coaching", "Running & Endurance Coaching"
    HEALTH_WELLNESS = "Health & Wellness Integration", "Health & Wellness Integration"
    WEIGHT_LOSS = "Weight Loss / Fat Loss Programs", "Weight Loss / Fat Loss Programs"
    MUSCLE_HYPERTROPHY = "Muscle Hypertrophy", "Muscle Hypertrophy"
    NUTRITION_COACHING = "Nutrition Coaching", "Nutrition Coaching"
    STRESS_MANAGEMENT = "Stress Management & Mind-Body Training", "Stress Management & Mind-Body Training"
    HOLISTIC_FITNESS = "Holistic Fitness", "Holistic Fitness"
    NICHE_LIFESTYLE = "Niche & Lifestyle-Oriented", "Niche & Lifestyle-Oriented"
    ONLINE_VIRTUAL = "Online / Virtual Fitness Coaching", "Online / Virtual Fitness Coaching"
    OUTDOOR_ADVENTURE = "Outdoor / Adventure Training", "Outdoor / Adventure Training"
    WORKPLACE_WELLNESS = "Workplace / Corporate Wellness", "Workplace / Corporate Wellness"
    GROUP_FITNESS = "Group Fitness Leadership", "Group Fitness Leadership"
    MILITARY_TACTICAL = "Military / Tactical Fitness", "Military / Tactical Fitness"


class AvailabilityDay(models.TextChoices):
    MONDAY = "Monday", "Monday"
    TUESDAY = "Tuesday", "Tuesday"
    WEDNESDAY = "Wednesday", "Wednesday"
    THURSDAY = "Thursday", "Thursday"
    FRIDAY = "Friday", "Friday"
    SATURDAY = "Saturday", "Saturday"
    SUNDAY = "Sunday", "Sunday"


class Expert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    photo = models.URLField(blank=True)
    expertise = models.CharField(max_length=64, choices=Expertise.choices)
    specialities = ArrayField(
        base_field=models.CharField(max_length=128, choices=Speciality.choices),
        blank=False,
        default=list,
    )
    availability_days = ArrayField(
        base_field=models.CharField(max_length=9, choices=AvailabilityDay.choices),
        blank=True,
        default=list,
    )
    availability_hours = ArrayField(
        base_field=models.PositiveSmallIntegerField(
            validators=[MinValueValidator(0), MaxValueValidator(23)]
        ),
        blank=True,
        default=list,
    )

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Client(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    photo = models.CharField(max_length=255, blank=True)
    birthdate = models.DateField(blank=True, null=True)
    objective = models.TextField()

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Appointment(models.Model):
    time = models.DateTimeField()
    client = models.ForeignKey(Client, related_name="appointments", on_delete=models.CASCADE)
    expert = models.ForeignKey(Expert, related_name="appointments", on_delete=models.CASCADE)

    class Meta:
        ordering = ["time"]

    def __str__(self) -> str:
        return f"{self.client} with {self.expert} at {self.time:%Y-%m-%d %H:%M}"
