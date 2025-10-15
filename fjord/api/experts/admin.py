from django import forms
from django.contrib import admin

from .models import Appointment, AvailabilityDay, Client, Expert, Speciality


_HOUR_CHOICES = [(str(hour), f"{hour:02d}:00") for hour in range(24)]


class ExpertAdminForm(forms.ModelForm):
    specialities = forms.MultipleChoiceField(
        choices=Speciality.choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Specialities",
        help_text="Select all specialities that apply to the expert.",
    )
    availability_days = forms.MultipleChoiceField(
        choices=AvailabilityDay.choices,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Availability days",
        help_text="Days of the week the expert accepts sessions.",
    )
    availability_hours = forms.MultipleChoiceField(
        choices=_HOUR_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Availability hours",
        help_text="Hours of the day (0-23) the expert is available.",
    )

    class Meta:
        model = Expert
        fields = [
            "name",
            "photo",
            "expertise",
            "specialities",
            "availability_days",
            "availability_hours",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self.instance, "specialities", None):
            self.initial["specialities"] = list(self.instance.specialities)
        if getattr(self.instance, "availability_days", None):
            self.initial["availability_days"] = list(self.instance.availability_days)
        if getattr(self.instance, "availability_hours", None):
            self.initial["availability_hours"] = [
                str(value) for value in self.instance.availability_hours
            ]

    def clean_specialities(self):
        values = self.cleaned_data["specialities"]
        return list(dict.fromkeys(values))

    def clean_availability_days(self):
        values = self.cleaned_data["availability_days"]
        return list(dict.fromkeys(values))

    def clean_availability_hours(self):
        raw_values = self.cleaned_data["availability_hours"]
        hours = []
        for value in raw_values:
            hour = int(value)
            if hour < 0 or hour > 23:
                raise forms.ValidationError("Hours must be between 0 and 23.")
            if hour not in hours:
                hours.append(hour)
        return hours


@admin.register(Expert)
class ExpertAdmin(admin.ModelAdmin):
    form = ExpertAdminForm
    list_display = ("name", "expertise")
    search_fields = ("name",)
    list_filter = ("expertise",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("time", "client", "expert")
    list_filter = ("time",)
