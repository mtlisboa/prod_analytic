from datetime import date
from typing import Any

import strawberry
from strawberry.scalars import JSON
from strawberry.types import Info

from .domain import Aggregation, AnalyticsField, FIELDS, FUNCTION_LABELS, TimePeriod
from .services import build_comparison_analysis, build_time_analysis


@strawberry.type
class FunctionOption:
    key: str
    label: str


@strawberry.type
class AnalysisField:
    key: str
    label: str
    kind: str
    unit: str
    groupable: bool
    supported_functions: list[FunctionOption]


@strawberry.type
class CatalogItem:
    id: strawberry.ID
    name: str


@strawberry.type
class AnalysisCatalog:
    exercises: list[CatalogItem]
    techniques: list[CatalogItem]


@strawberry.type
class ChartAxis:
    label: str
    unit: str
    kind: str


@strawberry.type
class ChartPoint:
    x: JSON
    y: JSON


@strawberry.type
class ChartSeries:
    label: str
    points: list[ChartPoint]


@strawberry.type
class ChartResult:
    x: ChartAxis
    y: ChartAxis
    series: list[ChartSeries]


@strawberry.input
class AxisInput:
    field: AnalyticsField
    function: Aggregation = Aggregation.RAW


@strawberry.input
class TimeAnalysisInput:
    start_date: date
    end_date: date
    period: TimePeriod
    lines: list[AxisInput]
    group_by: list[AnalyticsField] = strawberry.field(default_factory=list)
    exercise_ids: list[strawberry.ID] = strawberry.field(default_factory=list)
    technique_id: strawberry.ID | None = None


@strawberry.input
class ComparisonAnalysisInput:
    start_date: date
    end_date: date
    x: AxisInput
    y: AxisInput
    group_by: list[AnalyticsField] = strawberry.field(default_factory=list)
    exercise_ids: list[strawberry.ID] = strawberry.field(default_factory=list)
    technique_id: strawberry.ID | None = None


def _user(info: Info):
    request = getattr(info.context, "request", info.context)
    if not request.user.is_authenticated:
        raise PermissionError("Autenticação necessária.")
    return request.user


def _chart_result(payload: dict[str, Any]) -> ChartResult:
    return ChartResult(
        x=ChartAxis(**payload["x"]), y=ChartAxis(**payload["y"]),
        series=[
            ChartSeries(label=item["label"], points=[ChartPoint(**point) for point in item["points"]])
            for item in payload["series"]
        ],
    )


@strawberry.type
class Query:
    @strawberry.field(description="Lista todos os campos analíticos e as funções aceitas por cada campo.")
    def analysis_fields(self, info: Info) -> list[AnalysisField]:
        _user(info)
        return [
            AnalysisField(
                key=field.name, label=definition.label, kind=definition.kind,
                unit=definition.unit, groupable=definition.groupable,
                supported_functions=[FunctionOption(key=function.name, label=FUNCTION_LABELS[function]) for function in definition.supported_functions],
            )
            for field, definition in FIELDS.items()
        ]

    @strawberry.field(description="Lista os exercícios e técnicas disponíveis para filtros analíticos.")
    def analysis_catalog(self, info: Info) -> AnalysisCatalog:
        user = _user(info)
        return AnalysisCatalog(
            exercises=[CatalogItem(id=str(item.pk), name=item.name) for item in user.exercises.filter(active=True)],
            techniques=[CatalogItem(id=str(item.pk), name=item.name) for item in user.advanced_techniques.all()],
        )

    @strawberry.field(description="Gera séries temporais diárias, semanais ou mensais com várias linhas e classes.")
    def time_analysis(self, info: Info, input: TimeAnalysisInput) -> ChartResult:
        payload = build_time_analysis(
            user=_user(info), start_date=input.start_date, end_date=input.end_date,
            period=input.period, lines=input.lines, group_by=input.group_by,
            exercise_ids=[int(value) for value in input.exercise_ids],
            technique_id=int(input.technique_id) if input.technique_id else None,
        )
        return _chart_result(payload)

    @strawberry.field(description="Compara dois campos com funções independentes e múltiplas classes de agrupamento.")
    def comparison_analysis(self, info: Info, input: ComparisonAnalysisInput) -> ChartResult:
        payload = build_comparison_analysis(
            user=_user(info), start_date=input.start_date, end_date=input.end_date,
            x=input.x, y=input.y, group_by=input.group_by,
            exercise_ids=[int(value) for value in input.exercise_ids],
            technique_id=int(input.technique_id) if input.technique_id else None,
        )
        return _chart_result(payload)


schema = strawberry.Schema(query=Query)
