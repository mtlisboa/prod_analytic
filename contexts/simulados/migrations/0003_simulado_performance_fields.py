import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


def populate_performance_fields(apps, schema_editor):
    Simulado = apps.get_model("simulados", "Simulado")
    Intervalo = apps.get_model("simulados", "Intervalo")
    for simulation in Simulado.objects.all():
        rested = sum(Intervalo.objects.filter(simulado_id=simulation.pk).values_list("duration_minutes", flat=True))
        rested = min(rested, max(simulation.total_time_minutes - 1, 0))
        simulation.subject = "GERAL"
        simulation.rested_time_minutes = rested
        simulation.effective_time_minutes = simulation.total_time_minutes - rested
        simulation.save(update_fields=("subject", "rested_time_minutes", "effective_time_minutes"))


class Migration(migrations.Migration):
    dependencies = [("simulados", "0002_meta_metamateria")]
    operations = [
        migrations.AddField(
            model_name="simulado",
            name="meta",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="simulations", to="simulados.meta", verbose_name="prova visada"),
        ),
        migrations.AddField(
            model_name="simulado",
            name="subject",
            field=models.CharField(default="GERAL", max_length=120, validators=[django.core.validators.RegexValidator(message="Use apenas letras sem acentos, números e espaços.", regex="^[A-Za-zÀ-ÖØ-öø-ÿ0-9 ]+$")], verbose_name="matéria"),
        ),
        migrations.AddField(model_name="simulado", name="effective_time_minutes", field=models.PositiveIntegerField(null=True, verbose_name="tempo efetivo (minutos)")),
        migrations.AddField(model_name="simulado", name="rested_time_minutes", field=models.PositiveIntegerField(default=0, verbose_name="tempo descansado (minutos)")),
        migrations.RunPython(populate_performance_fields, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="simulado",
            name="effective_time_minutes",
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name="tempo efetivo (minutos)"),
        ),
        migrations.AlterField(
            model_name="metamateria",
            name="subject",
            field=models.CharField(max_length=120, validators=[django.core.validators.RegexValidator(message="Use apenas letras sem acentos, números e espaços.", regex="^[A-Za-zÀ-ÖØ-öø-ÿ0-9 ]+$")], verbose_name="matéria"),
        ),
    ]
