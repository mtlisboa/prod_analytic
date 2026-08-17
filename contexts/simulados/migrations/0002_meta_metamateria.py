import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("simulados", "0001_initial"),
    ]
    operations = [
        migrations.CreateModel(
            name="Meta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("exam_name", models.CharField(max_length=180, verbose_name="prova")),
                ("exam_date", models.DateField(blank=True, null=True, verbose_name="data da prova")),
                ("exam_time_minutes", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="tempo-alvo de prova (minutos)")),
                ("break_time_minutes", models.PositiveIntegerField(default=0, verbose_name="tempo-alvo de descanso (minutos)")),
                ("observation", models.TextField(blank=True, verbose_name="observações")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="metas_simulados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": (models.F("exam_date").asc(nulls_last=True), "-created_at")},
        ),
        migrations.CreateModel(
            name="MetaMateria",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("subject", models.CharField(max_length=120, verbose_name="matéria")),
                ("target_accuracy_percent", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)], verbose_name="aproveitamento-alvo (%)")),
                ("position", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="ordem")),
                ("meta", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="subjects", to="simulados.meta")),
            ],
            options={"ordering": ("position",)},
        ),
        migrations.AddConstraint(
            model_name="metamateria",
            constraint=models.UniqueConstraint(fields=("meta", "position"), name="unique_meta_subject_position"),
        ),
    ]
