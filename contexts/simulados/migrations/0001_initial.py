import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="Simulado",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180, verbose_name="nome do simulado")),
                ("exam_date", models.DateField(verbose_name="data de realização")),
                ("exam_url", models.URLField(blank=True, verbose_name="link da prova")),
                ("total_questions", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="total de questões")),
                ("correct_answers", models.PositiveIntegerField(default=0, verbose_name="questões acertadas")),
                ("wrong_answers", models.PositiveIntegerField(default=0, verbose_name="questões erradas")),
                ("observation", models.TextField(blank=True, verbose_name="impressões sobre a prova")),
                ("total_time_minutes", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="tempo total (minutos)")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="simulados", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-exam_date", "-created_at")},
        ),
        migrations.CreateModel(
            name="Intervalo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="ordem")),
                ("duration_minutes", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="duração (minutos)")),
                ("note", models.CharField(blank=True, max_length=180, verbose_name="observação")),
                ("simulado", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="intervals", to="simulados.simulado")),
            ],
            options={"ordering": ("position",)},
        ),
        migrations.AddConstraint(
            model_name="intervalo",
            constraint=models.UniqueConstraint(fields=("simulado", "position"), name="unique_simulado_interval_position"),
        ),
    ]
