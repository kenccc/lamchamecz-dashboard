import re

from django.db import migrations, models


def parse_to_int(apps, schema_editor):
    Student = apps.get_model("core", "Student")
    for s in Student.objects.all():
        raw = (s.birth_year or "").strip()
        m = re.search(r"\d{1,4}", raw)
        if m:
            try:
                val = int(m.group(0))
                if 0 < val < 32768:
                    s.birth_year_int = val
                    s.save(update_fields=["birth_year_int"])
            except ValueError:
                pass


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_alter_classroom_assistant_alter_classroom_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="birth_year_int",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.RunPython(parse_to_int, noop_reverse),
        migrations.RemoveField(
            model_name="student",
            name="birth_year",
        ),
        migrations.RenameField(
            model_name="student",
            old_name="birth_year_int",
            new_name="birth_year",
        ),
        migrations.AlterField(
            model_name="student",
            name="birth_year",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Birth year"),
        ),
    ]
