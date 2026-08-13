import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="AdvancedTechnique",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="nome")),
                ("description", models.TextField(blank=True, verbose_name="descrição")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="advanced_techniques", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="Exercise",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="nome")),
                ("muscle_group", models.CharField(choices=[("chest", "Peito"), ("back", "Costas"), ("legs", "Pernas"), ("shoulders", "Ombros"), ("arms", "Braços"), ("core", "Core"), ("cardio", "Cardio"), ("other", "Outro")], max_length=20, verbose_name="grupo muscular")),
                ("active", models.BooleanField(default=True, verbose_name="ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exercises", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="TrainingRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("performed_at", models.DateTimeField(verbose_name="data e hora")),
                ("sets_count", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="número de séries")),
                ("execution_time_seconds", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="tempo total de execução (segundos)")),
                ("rest_time_seconds", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name="tempo total de descanso (segundos)")),
                ("weight_kg", models.DecimalField(decimal_places=2, max_digits=7, validators=[django.core.validators.MinValueValidator(0)], verbose_name="peso por série (kg)")),
                ("notes", models.CharField(blank=True, max_length=240, verbose_name="observações")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("advanced_technique", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="records", to="academia.advancedtechnique", verbose_name="técnica avançada")),
                ("exercise", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="records", to="academia.exercise", verbose_name="exercício")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="training_records", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-performed_at",)},
        ),
        migrations.AddConstraint(model_name="advancedtechnique", constraint=models.UniqueConstraint(fields=("user", "name"), name="unique_technique_per_user")),
        migrations.AddConstraint(model_name="exercise", constraint=models.UniqueConstraint(fields=("user", "name"), name="unique_exercise_per_user")),
    ]
