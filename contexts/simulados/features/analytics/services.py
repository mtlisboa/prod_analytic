from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from statistics import mean

from contexts.simulados.models import Simulado


@dataclass(frozen=True)
class FieldDefinition:
    label: str
    unit: str
    kind: str


FIELDS = {
    "date": FieldDefinition("Data", "", "category"),
    "subject": FieldDefinition("Matéria", "", "category"),
    "target_exam": FieldDefinition("Prova visada", "", "category"),
    "accuracy": FieldDefinition("Aproveitamento", "%", "number"),
    "total_questions": FieldDefinition("Total de questões", "questões", "number"),
    "correct_answers": FieldDefinition("Acertos", "questões", "number"),
    "wrong_answers": FieldDefinition("Erros", "questões", "number"),
    "effective_time": FieldDefinition("Tempo efetivo", "min", "number"),
    "rested_time": FieldDefinition("Tempo descansado", "min", "number"),
    "total_time": FieldDefinition("Tempo total", "min", "number"),
}

TIME_METRICS = (
    "accuracy", "correct_answers", "wrong_answers", "effective_time", "rested_time", "total_time",
)
X_FIELDS = tuple(FIELDS)
Y_FIELDS = tuple(key for key, definition in FIELDS.items() if definition.kind == "number")
AGGREGATIONS = {"avg": "Média", "sum": "Soma", "min": "Mínimo", "max": "Máximo", "count": "Quantidade"}
PERIODS = {"daily": "Diário", "weekly": "Semanal", "monthly": "Mensal"}
GROUPS = {"none": "Sem separação", "subject": "Matéria", "target_exam": "Prova visada"}


def filtered_simulations(*, user, start_date, end_date, subject="", meta_id=""):
    queryset = Simulado.objects.filter(user=user, exam_date__range=(start_date, end_date)).select_related("meta")
    if subject:
        queryset = queryset.filter(subject=subject)
    if meta_id:
        queryset = queryset.filter(meta_id=meta_id)
    return queryset.order_by("exam_date", "created_at")


def build_time_analysis(*, queryset, metrics, period, group_by):
    grouped = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    labels = {}
    for simulation in queryset:
        bucket, label = _time_bucket(simulation.exam_date, period)
        labels[bucket] = label
        group = _group_value(simulation, group_by)
        for metric in metrics:
            grouped[group][metric][bucket].append(_field_value(simulation, metric))

    bucket_keys = sorted(labels)
    series = []
    for group, metric_data in grouped.items():
        for metric in metrics:
            definition = FIELDS[metric]
            label = definition.label if group_by == "none" else f"{definition.label} · {group}"
            series.append({
                "label": label,
                "points": [
                    {"x": labels[bucket], "y": round(mean(metric_data[metric][bucket]), 2)}
                    for bucket in bucket_keys if metric_data[metric].get(bucket)
                ],
            })
    return {
        "x": {"label": "Tempo", "unit": "", "kind": "category"},
        "y": {"label": "Performance", "unit": "", "kind": "number"},
        "series": series,
    }


def build_dynamic_analysis(*, queryset, x_field, y_field, aggregation, group_by):
    groups = defaultdict(lambda: defaultdict(list))
    for simulation in queryset:
        group = _group_value(simulation, group_by)
        groups[group][_field_value(simulation, x_field)].append(_field_value(simulation, y_field))

    series = []
    for group, values_by_x in groups.items():
        points = [
            {"x": x_value, "y": _aggregate(values, aggregation)}
            for x_value, values in values_by_x.items()
        ]
        if FIELDS[x_field].kind == "number":
            points.sort(key=lambda point: float(point["x"]))
        series.append({"label": group, "points": points})

    y_definition = FIELDS[y_field]
    y_label = "Quantidade de simulados" if aggregation == "count" else f"{AGGREGATIONS[aggregation]} de {y_definition.label.lower()}"
    return {
        "x": FIELDS[x_field].__dict__,
        "y": {"label": y_label, "unit": "" if aggregation == "count" else y_definition.unit, "kind": "number"},
        "series": series,
    }


def _field_value(simulation, field):
    values = {
        "date": simulation.exam_date.strftime("%d/%m/%Y"),
        "subject": simulation.subject,
        "target_exam": simulation.meta.exam_name if simulation.meta else "SEM PROVA VISADA",
        "accuracy": simulation.accuracy,
        "total_questions": simulation.total_questions,
        "correct_answers": simulation.correct_answers,
        "wrong_answers": simulation.wrong_answers,
        "effective_time": simulation.effective_time_minutes,
        "rested_time": simulation.rested_time_minutes,
        "total_time": simulation.total_time_minutes,
    }
    return values[field]


def _group_value(simulation, group_by):
    if group_by == "subject":
        return simulation.subject
    if group_by == "target_exam":
        return simulation.meta.exam_name if simulation.meta else "SEM PROVA VISADA"
    return "Simulados"


def _time_bucket(value: date, period):
    if period == "weekly":
        monday = value.fromordinal(value.toordinal() - value.weekday())
        return monday.isoformat(), f"Semana de {monday:%d/%m}"
    if period == "monthly":
        return value.strftime("%Y-%m"), value.strftime("%m/%Y")
    return value.isoformat(), value.strftime("%d/%m/%Y")


def _aggregate(values, aggregation):
    if aggregation == "sum":
        value = sum(values)
    elif aggregation == "min":
        value = min(values)
    elif aggregation == "max":
        value = max(values)
    elif aggregation == "count":
        value = len(values)
    else:
        value = mean(values)
    return round(value, 2)
