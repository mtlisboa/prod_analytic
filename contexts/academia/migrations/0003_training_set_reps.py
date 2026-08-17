import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("academia", "0002_training_sets")]

    operations = [
        migrations.AddField(
            model_name="trainingset",
            name="reps",
            field=models.PositiveIntegerField(
                default=0,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="repetições totais",
            ),
        ),
        migrations.AddField(
            model_name="trainingset",
            name="partial_reps",
            field=models.PositiveIntegerField(
                default=0,
                validators=[django.core.validators.MinValueValidator(0)],
                verbose_name="repetições parciais",
            ),
        ),
        migrations.AddConstraint(
            model_name="trainingset",
            constraint=models.CheckConstraint(
                condition=models.Q(partial_reps__lte=models.F("reps")),
                name="partial_reps_lte_reps",
            ),
        ),
    ]
