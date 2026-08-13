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


METRICS = {
    "sets": MetricDefinition("Número de séries", "séries", Count("id")),
    "rest_time": MetricDefinition("Tempo total de descanso", "min", Sum("rest_time_seconds")),
    "weight_per_set": MetricDefinition("Peso médio por série", "kg", Avg("weight_kg")),
    "rest_per_set": MetricDefinition("Descanso médio por série", "s", Avg("rest_time_seconds")),
    "execution_per_set": MetricDefinition("Execução média por série", "s", Avg("execution_time_seconds")),
}
TRUNCATORS = {"daily": TruncDay, "weekly": TruncWeek, "monthly": TruncMonth}


def _date_bounds(start: date, end: date):
    tz = timezone.get_current_timezone()
    return timezone.make_aware(datetime.combine(start, time.min), tz), timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min), tz)


def build_analysis(*, user, start_date, end_date, period, metric, technique=None):
    start, end_exclusive = _date_bounds(start_date, end_date)
    queryset = TrainingSet.objects.filter(training_record__user=user, performed_at__gte=start, performed_at__lt=end_exclusive)
    if technique:
        queryset = queryset.filter(advanced_technique=technique)
    definition = METRICS[metric]
    rows = list(queryset.annotate(bucket=TRUNCATORS[period]("performed_at")).values("bucket").annotate(value=definition.aggregate, records=Count("training_record_id", distinct=True)).order_by("bucket"))
    for row in rows:
        value = float(row["value"] or 0)
        if metric == "rest_time": value /= 60
        row["value"] = round(value, 2)
        row["label"] = _format_bucket(row["bucket"], period)
    return rows, definition


def _format_bucket(value, period):
    local_value = timezone.localtime(value)
    if period == "daily": return local_value.strftime("%d/%m/%Y")
    if period == "weekly": return f"Semana de {local_value:%d/%m}"
    return local_value.strftime("%m/%Y")
