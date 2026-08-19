from collections import defaultdict
from datetime import date, datetime, time, timedelta

from django.utils import timezone

from contexts.academia.features.training.models import TrainingSet

from .domain import Aggregation, AnalyticsField, FIELDS, FUNCTION_LABELS, TimePeriod


def _date_bounds(start_date: date, end_date: date):
    tz = timezone.get_current_timezone()
    return (
        timezone.make_aware(datetime.combine(start_date, time.min), tz),
        timezone.make_aware(datetime.combine(end_date + timedelta(days=1), time.min), tz),
    )


def _querysets(*, user, start_date, end_date, exercise_ids=None, technique_id=None):
    if start_date > end_date:
        raise ValueError("A data final deve ser igual ou posterior à data inicial.")
    start, end_exclusive = _date_bounds(start_date, end_date)
    queryset = TrainingSet.objects.filter(
        training_record__user=user,
        performed_at__gte=start,
        performed_at__lt=end_exclusive,
    ).select_related("training_record__exercise", "advanced_technique")
    if exercise_ids:
        queryset = queryset.filter(training_record__exercise_id__in=exercise_ids)
    if technique_id:
        queryset = queryset.filter(advanced_technique_id=technique_id)
    return queryset.order_by("performed_at", "training_record_id", "position")


def _value(training_set, field):
    if field is AnalyticsField.EXERCISE:
        return training_set.training_record.exercise.name
    if field is AnalyticsField.SET_POSITION:
        return training_set.position
    if field is AnalyticsField.WEIGHT:
        return float(training_set.weight_kg)
    if field is AnalyticsField.EXECUTION:
        return training_set.execution_time_seconds
    if field is AnalyticsField.REST:
        return training_set.rest_time_seconds
    if field is AnalyticsField.TECHNIQUE:
        return training_set.advanced_technique.name if training_set.advanced_technique else "Sem técnica"
    return timezone.localtime(training_set.performed_at).strftime("%d/%m/%Y")


def _validate(field, function):
    if function not in FIELDS[field].supported_functions:
        raise ValueError(f"A função {function.name} não é permitida para {field.name}.")


def _aggregate(values, function):
    if not values:
        return 0
    if function is Aggregation.RAW:
        return values[-1]
    if function is Aggregation.COUNT:
        return len(values)
    numeric = [float(value) for value in values]
    if function is Aggregation.SUM:
        result = sum(numeric)
    elif function is Aggregation.AVG:
        result = sum(numeric) / len(numeric)
    elif function is Aggregation.MIN:
        result = min(numeric)
    else:
        result = max(numeric)
    return round(result, 2)


def _axis(field, function):
    definition = FIELDS[field]
    is_numeric = definition.kind == "NUMBER" or function is not Aggregation.RAW
    label = definition.label if function is Aggregation.RAW else f"{FUNCTION_LABELS[function]} de {definition.label}"
    unit = "registros" if function is Aggregation.COUNT else definition.unit
    return {"label": label, "unit": unit, "kind": "number" if is_numeric else "category"}


def _group_label(training_set, group_by):
    if not group_by:
        return "Dados"
    return " · ".join(str(_value(training_set, field)) for field in group_by)


def _time_bucket(training_set, period):
    performed = timezone.localtime(training_set.performed_at)
    if period is TimePeriod.DAILY:
        key = performed.date()
        return key, key.strftime("%d/%m/%Y")
    if period is TimePeriod.WEEKLY:
        key = performed.date() - timedelta(days=performed.weekday())
        return key, f"Semana de {key:%d/%m}"
    key = performed.date().replace(day=1)
    return key, key.strftime("%m/%Y")


def build_time_analysis(*, user, start_date, end_date, period, lines, group_by, exercise_ids=None, technique_id=None):
    for line in lines:
        _validate(line.field, line.function)
    records = list(_querysets(
        user=user, start_date=start_date, end_date=end_date,
        exercise_ids=exercise_ids, technique_id=technique_id,
    ))
    buckets = {}
    grouped = defaultdict(list)
    for training_set in records:
        bucket_key, bucket_label = _time_bucket(training_set, period)
        buckets[bucket_key] = bucket_label
        grouped[(bucket_key, _group_label(training_set, group_by))].append(training_set)

    ordered_buckets = sorted(buckets)
    group_labels = list(dict.fromkeys(key[1] for key in grouped)) or ["Dados"]
    series = []
    for line in lines:
        definition = FIELDS[line.field]
        for group_label in group_labels:
            values = []
            for bucket_key in ordered_buckets:
                items = grouped.get((bucket_key, group_label), [])
                values.append(_aggregate([_value(item, line.field) for item in items], line.function))
            line_label = definition.label if line.function is Aggregation.RAW else f"{FUNCTION_LABELS[line.function]} de {definition.label}"
            if group_by:
                line_label = f"{line_label} · {group_label}"
            series.append({
                "label": line_label,
                "points": [{"x": buckets[key], "y": value} for key, value in zip(ordered_buckets, values)],
            })
    return {
        "x": {"label": "Tempo", "unit": "", "kind": "category"},
        "y": {"label": "Valores", "unit": "", "kind": "number"},
        "series": series,
    }


def _comparison_points(items, x, y):
    if x.function is Aggregation.RAW and y.function is Aggregation.RAW:
        return [{"x": _value(item, x.field), "y": _value(item, y.field)} for item in items]
    if x.function is Aggregation.RAW:
        buckets = defaultdict(list)
        for item in items:
            buckets[str(_value(item, x.field))].append(item)
        return [
            {"x": _value(bucket[0], x.field), "y": _aggregate([_value(item, y.field) for item in bucket], y.function)}
            for bucket in buckets.values()
        ]
    if y.function is Aggregation.RAW:
        buckets = defaultdict(list)
        for item in items:
            buckets[str(_value(item, y.field))].append(item)
        return [
            {"x": _aggregate([_value(item, x.field) for item in bucket], x.function), "y": _value(bucket[0], y.field)}
            for bucket in buckets.values()
        ]
    return [{
        "x": _aggregate([_value(item, x.field) for item in items], x.function),
        "y": _aggregate([_value(item, y.field) for item in items], y.function),
    }]


def build_comparison_analysis(*, user, start_date, end_date, x, lines, group_by, exercise_ids=None, technique_id=None):
    _validate(x.field, x.function)
    for line in lines:
        _validate(line.field, line.function)
    records = list(_querysets(
        user=user, start_date=start_date, end_date=end_date,
        exercise_ids=exercise_ids, technique_id=technique_id,
    ))
    line_groups = defaultdict(list)
    for training_set in records:
        line_groups[_group_label(training_set, group_by)].append(training_set)

    series = []
    multiple_lines = len(lines) > 1
    for line in lines:
        line_axis = _axis(line.field, line.function)
        for group_label, items in line_groups.items():
            label = line_axis["label"] if multiple_lines else group_label
            if group_by and multiple_lines:
                label = f'{line_axis["label"]} · {group_label}'
            series.append({"label": label, "points": _comparison_points(items, x, line)})

    y_axis = _axis(lines[0].field, lines[0].function) if len(lines) == 1 else {
        "label": "Valores", "unit": "", "kind": "number",
    }
    return {"x": _axis(x.field, x.function), "y": y_axis, "series": series}
