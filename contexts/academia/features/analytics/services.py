from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDay, TruncMonth, TruncWeek
from django.utils import timezone

from contexts.academia.features.training.models import TrainingSet


@dataclass(frozen=True)
class MetricDefinition:
    label: str
    unit: str
    aggregate: object


@dataclass(frozen=True)
class AxisDefinition:
    label: str
    unit: str
    kind: str


METRICS = {
    "sets": MetricDefinition("Número de séries", "séries", Count("id")),
    "rest_time": MetricDefinition("Tempo total de descanso", "min", Sum("rest_time_seconds")),
    "weight_per_set": MetricDefinition("Peso médio por série", "kg", Avg("weight_kg")),
    "rest_per_set": MetricDefinition("Descanso médio por série", "s", Avg("rest_time_seconds")),
    "execution_per_set": MetricDefinition("Execução média por série", "s", Avg("execution_time_seconds")),
}
TRUNCATORS = {"daily": TruncDay, "weekly": TruncWeek, "monthly": TruncMonth}
AXES = {
    "exercise": AxisDefinition("Exercício", "", "category"),
    "set_position": AxisDefinition("Número da série", "série", "number"),
    "weight": AxisDefinition("Força / carga", "kg", "number"),
    "execution": AxisDefinition("Tempo de execução", "s", "number"),
    "rest": AxisDefinition("Tempo de descanso", "s", "number"),
    "technique": AxisDefinition("Técnica", "", "category"),
    "date": AxisDefinition("Data", "", "category"),
}


def _date_bounds(start: date, end: date):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(start, time.min), tz), timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), tz)


def build_analysis(*, user, start_date, end_date, period, metric, technique=None, exercises=None):
    start, end_exclusive = _date_bounds(start_date, end_date)
    queryset = TrainingSet.objects.filter(training_record__user=user, performed_at__gte=start, performed_at__lt=end_exclusive)
    if technique:
        queryset = queryset.filter(advanced_technique=technique)
    if exercises:
        queryset = queryset.filter(training_record__exercise__in=exercises)
    definition = METRICS[metric]
    rows = list(queryset.annotate(bucket=TRUNCATORS[period]("performed_at")).values("bucket").annotate(value=definition.aggregate, records=Count("training_record_id", distinct=True)).order_by("bucket"))
    for row in rows:
        value = float(row["value"] or 0)
        if metric == "rest_time": value /= 60
        row["value"] = round(value, 2)
        row["label"] = _format_bucket(row["bucket"], period)
    return rows, definition


def build_multi_analysis(*, user, start_date, end_date, period, metrics, technique=None):
    """Return aligned time buckets for every selected metric."""
    series = []
    buckets = {}
    for metric_key in metrics:
        rows, definition = build_analysis(
            user=user,
            start_date=start_date,
            end_date=end_date,
            period=period,
            metric=metric_key,
            technique=technique,
        )
        values = {row["bucket"].isoformat(): row for row in rows}
        buckets.update({key: row["label"] for key, row in values.items()})
        series.append({
            "key": metric_key,
            "label": definition.label,
            "unit": definition.unit,
            "values_by_bucket": values,
        })

    bucket_keys = sorted(buckets)
    for item in series:
        values_by_bucket = item.pop("values_by_bucket")
        item["values"] = [
            values_by_bucket.get(key, {}).get("value", 0)
            for key in bucket_keys
        ]
    return [buckets[key] for key in bucket_keys], series


def build_time_analysis(*, user, start_date, end_date, period, metrics, technique=None, exercises=None):
    """Build one time line for every metric/exercise combination."""
    selected_exercises = list(exercises or [])
    combinations = [None] if not selected_exercises else selected_exercises
    raw_series = []
    buckets = {}
    for exercise in combinations:
        for metric_key in metrics:
            rows, definition = build_analysis(
                user=user, start_date=start_date, end_date=end_date,
                period=period, metric=metric_key, technique=technique,
                exercises=[exercise] if exercise else None,
            )
            values = {row["bucket"].isoformat(): row for row in rows}
            buckets.update({key: row["label"] for key, row in values.items()})
            label = definition.label
            if exercise:
                label = f"{definition.label} · {exercise.name}"
            raw_series.append({
                "key": f"{metric_key}-{exercise.pk if exercise else 'all'}",
                "label": label, "unit": definition.unit,
                "values_by_bucket": values,
            })
    bucket_keys = sorted(buckets)
    for item in raw_series:
        values_by_bucket = item.pop("values_by_bucket")
        item["values"] = [values_by_bucket.get(key, {}).get("value", 0) for key in bucket_keys]
    return [buckets[key] for key in bucket_keys], raw_series


def _axis_value(training_set, axis):
    if axis == "exercise":
        return training_set.training_record.exercise.name
    if axis == "set_position":
        return training_set.position
    if axis == "weight":
        return float(training_set.weight_kg)
    if axis == "execution":
        return training_set.execution_time_seconds
    if axis == "rest":
        return training_set.rest_time_seconds
    if axis == "technique":
        return training_set.advanced_technique.name if training_set.advanced_technique else "Sem técnica"
    return timezone.localtime(training_set.performed_at).strftime("%d/%m/%Y")


def build_comparison(*, user, start_date, end_date, x_axis, y_axis, technique=None, exercises=None, group_by=""):
    """Build raw X/Y lines without forcing either axis to be time-based."""
    start, end_exclusive = _date_bounds(start_date, end_date)
    queryset = TrainingSet.objects.filter(
        training_record__user=user, performed_at__gte=start, performed_at__lt=end_exclusive,
    ).select_related("training_record__exercise", "advanced_technique")
    if technique:
        queryset = queryset.filter(advanced_technique=technique)
    if exercises:
        queryset = queryset.filter(training_record__exercise__in=exercises)

    groups = {}
    for training_set in queryset.order_by("performed_at", "training_record_id", "position"):
        if group_by == "exercise":
            group = training_set.training_record.exercise.name
        elif group_by == "technique":
            group = training_set.advanced_technique.name if training_set.advanced_technique else "Sem técnica"
        else:
            group = "Dados"
        groups.setdefault(group, []).append({
            "x": _axis_value(training_set, x_axis),
            "y": _axis_value(training_set, y_axis),
        })

    return {
        "x": AXES[x_axis].__dict__,
        "y": AXES[y_axis].__dict__,
        "series": [{"label": label, "points": points} for label, points in groups.items()],
    }


def _format_bucket(value, period):
    local_value = timezone.localtime(value)
    if period == "daily": return local_value.strftime("%d/%m/%Y")
    if period == "weekly": return f"Semana de {local_value:%d/%m}"
    return local_value.strftime("%m/%Y")
