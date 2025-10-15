from django.forms.widgets import CheckboxSelectMultiple
from django.test import SimpleTestCase

from experts.admin import ExpertAdminForm
from experts.models import AvailabilityDay, Expert, Expertise, Speciality


class ExpertAdminFormTests(SimpleTestCase):
    def test_specialities_field_uses_checkbox_widget(self):
        form = ExpertAdminForm()
        field = form.fields["specialities"]

        self.assertIsInstance(field.widget, CheckboxSelectMultiple)
        self.assertEqual(field.choices, Speciality.choices)

    def test_availability_fields_use_checkboxes(self):
        form = ExpertAdminForm()

        self.assertIsInstance(form.fields["availability_days"].widget, CheckboxSelectMultiple)
        self.assertEqual(form.fields["availability_days"].choices, AvailabilityDay.choices)

        self.assertIsInstance(form.fields["availability_hours"].widget, CheckboxSelectMultiple)
        self.assertEqual(len(form.fields["availability_hours"].choices), 24)

    def test_initial_fields_populated_from_instance(self):
        instance = Expert(
            name="Test Expert",
            photo="https://example.com/photo.jpg",
            expertise=Expertise.PERSONAL_TRAINER,
            specialities=[Speciality.WEIGHT_LOSS, Speciality.NUTRITION_COACHING],
            availability_days=[AvailabilityDay.MONDAY, AvailabilityDay.FRIDAY],
            availability_hours=[8, 14],
        )

        form = ExpertAdminForm(instance=instance)

        self.assertEqual(
            form.initial["specialities"],
            [Speciality.WEIGHT_LOSS, Speciality.NUTRITION_COACHING],
        )
        self.assertEqual(
            form.initial["availability_days"],
            [AvailabilityDay.MONDAY, AvailabilityDay.FRIDAY],
        )
        self.assertEqual(form.initial["availability_hours"], ["8", "14"])

    def test_clean_methods_deduplicate_values(self):
        form = ExpertAdminForm(
            data={
                "name": "Another Expert",
                "photo": "https://example.com/photo.jpg",
                "expertise": Expertise.PERSONAL_TRAINER,
                "specialities": [
                    Speciality.WEIGHT_LOSS.value,
                    Speciality.WEIGHT_LOSS.value,
                    Speciality.NUTRITION_COACHING.value,
                ],
                "availability_days": [
                    AvailabilityDay.MONDAY.value,
                    AvailabilityDay.MONDAY.value,
                    AvailabilityDay.SATURDAY.value,
                ],
                "availability_hours": ["8", "8", "15"],
            }
        )

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["specialities"],
            [Speciality.WEIGHT_LOSS.value, Speciality.NUTRITION_COACHING.value],
        )
        self.assertEqual(
            form.cleaned_data["availability_days"],
            [AvailabilityDay.MONDAY.value, AvailabilityDay.SATURDAY.value],
        )
        self.assertEqual(form.cleaned_data["availability_hours"], [8, 15])
