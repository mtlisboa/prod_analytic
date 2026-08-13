import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def split_existing_records(apps, schema_editor):
    TrainingRecord = apps.get_model("academia", "TrainingRecord")
    TrainingSet = apps.get_model("academia", "TrainingSet")
    for record in TrainingRecord.objects.all().iterator():
        count = max(record.sets_count, 1)
        execution_base, execution_remainder = divmod(record.execution_time_seconds, count)
        rest_base, rest_remainder = divmod(record.rest_time_seconds, count)
        for index in range(count):
            TrainingSet.objects.create(
                training_record=record,
                position=index + 1,
                performed_at=record.performed_at,
                weight_kg=record.weight_kg,
                execution_time_seconds=execution_base + (1 if index < execution_remainder else 0),
                rest_time_seconds=rest_base + (1 if index < rest_remainder else 0),
                advanced_technique_id=record.advanced_technique_id,
                notes=record.notes,
            )


class Migration(migrations.Migration):
    dependencies = [("academia", "0001_initial")]
    operations = [
        migrations.CreateModel(
            name="TrainingSet",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("position", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="número da série")),
                ("performed_at", models.DateTimeField(verbose_name="data e hora")),
                ("weight_kg", models.DecimalField(decimal_places=2, max_digits=7, validators=[django.core.validators.MinValueValidator(0)], verbose_name="peso (kg)")),
                ("execution_time_seconds", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="tempo de execução (segundos)")),
                ("rest_time_seconds", models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(0)], verbose_name="tempo de descanso (segundos)")),
                ("notes", models.CharField(blank=True, max_length=240, verbose_name="observações")),
                ("advanced_technique", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="training_sets", to="academia.advancedtechnique", verbose_name="técnica avançada")),
                ("training_record", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sets", to="academia.trainingrecord")),
            ],
            options={"ordering": ("position",)},
        ),
        migrations.AddConstraint(model_name="trainingset", constraint=models.UniqueConstraint(fields=("training_record", "position"), name="unique_set_position")),
        migrations.RunPython(split_existing_records, migrations.RunPython.noop),
        migrations.RemoveField(model_name="trainingrecord", name="advanced_technique"),
        migrations.RemoveField(model_name="trainingrecord", name="execution_time_seconds"),
        migrations.RemoveField(model_name="trainingrecord", name="notes"),
        migrations.RemoveField(model_name="trainingrecord", name="performed_at"),
        migrations.RemoveField(model_name="trainingrecord", name="rest_time_seconds"),
        migrations.RemoveField(model_name="trainingrecord", name="sets_count"),
        migrations.RemoveField(model_name="trainingrecord", name="weight_kg"),
        migrations.AlterModelOptions(name="trainingrecord", options={"ordering": ("-created_at",)}),
    ]
