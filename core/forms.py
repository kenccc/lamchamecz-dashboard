from datetime import timedelta

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _

from .models import ClassRoom, ClassTime, DayOff, Enrollment, Role, Student, User

MAX_CLASS_SPAN_DAYS = 365 * 5


class StyledFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            cls = field.widget.attrs.get("class", "")
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = f"{cls} form-check-input".strip()
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = f"{cls} glass-input".strip()
            else:
                field.widget.attrs["class"] = f"{cls} glass-input".strip()


class UserForm(StyledFormMixin, UserCreationForm):
    fullname = forms.CharField(label=_("Full name"), max_length=255)
    role = forms.ChoiceField(label=_("Role"), choices=Role.choices)

    class Meta:
        model = User
        fields = ("username", "fullname", "role", "password1", "password2")


class ClassRoomForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClassRoom
        fields = (
            "code", "subject", "teacher", "assistant",
            "total_lessons", "minutes_per_lesson", "fee_per_lesson",
            "date_start", "date_end",
        )
        widgets = {
            "date_start": forms.DateInput(attrs={"type": "date"}),
            "date_end": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assistant"].queryset = User.objects.filter(role=Role.ASSISTANT)
        self.fields["assistant"].required = False
        if current_user is not None and not current_user.is_app_admin:
            del self.fields["teacher"]
        else:
            self.fields["teacher"].queryset = User.objects.filter(
                role__in=[Role.TEACHER, Role.ADMIN]
            )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("date_start")
        end = cleaned.get("date_end")
        if start and end:
            if end < start:
                raise forms.ValidationError(_("End date must be on or after start date."))
            if (end - start) > timedelta(days=MAX_CLASS_SPAN_DAYS):
                raise forms.ValidationError(
                    _("Class span exceeds %(years)d years.") % {"years": MAX_CLASS_SPAN_DAYS // 365}
                )
        return cleaned


class ClassTimeForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClassTime
        fields = ("weekday", "time_start", "time_end")
        widgets = {
            "time_start": forms.TimeInput(attrs={"type": "time"}),
            "time_end": forms.TimeInput(attrs={"type": "time"}),
        }


ClassTimeFormSet = forms.inlineformset_factory(
    ClassRoom, ClassTime, form=ClassTimeForm, extra=1, can_delete=True,
)


class StudentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Student
        fields = ("rodne_cislo", "name", "birth_year", "school_class", "contact", "note")


class EnrollmentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ("student", "classroom", "actual_lessons", "note")


class DayOffForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = DayOff
        fields = ("date",)
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}
