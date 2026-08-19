from dataclasses import dataclass
from enum import Enum

import strawberry


@strawberry.enum
class AnalyticsField(Enum):
    EXERCISE = "exercise"
    SET_POSITION = "set_position"
    WEIGHT = "weight"
    REPS = "reps"
    PARTIAL_REPS = "partial_reps"
    PARTIAL_REPS_RATIO = "partial_reps_ratio"
    NON_PARTIAL_REPS = "non_partial_reps"
    EXECUTION = "execution"
    REST = "rest"
    TECHNIQUE = "technique"
    DATE = "date"


@strawberry.enum
class Aggregation(Enum):
    RAW = "raw"
    COUNT = "count"
    SUM = "sum"
    AVG = "avg"
    MIN = "min"
    MAX = "max"


@strawberry.enum
class TimePeriod(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


@dataclass(frozen=True)
class FieldDefinition:
    label: str
    kind: str
    unit: str
    supported_functions: tuple[Aggregation, ...]
    groupable: bool = False


NUMERIC_FUNCTIONS = (
    Aggregation.RAW, Aggregation.COUNT, Aggregation.SUM,
    Aggregation.AVG, Aggregation.MIN, Aggregation.MAX,
)
CATEGORY_FUNCTIONS = (Aggregation.RAW, Aggregation.COUNT)

FIELDS = {
    AnalyticsField.EXERCISE: FieldDefinition("Exercício", "CATEGORY", "", CATEGORY_FUNCTIONS, True),
    AnalyticsField.SET_POSITION: FieldDefinition("Número da série", "NUMBER", "série", NUMERIC_FUNCTIONS, True),
    AnalyticsField.WEIGHT: FieldDefinition("Força / carga", "NUMBER", "kg", NUMERIC_FUNCTIONS),
    AnalyticsField.REPS: FieldDefinition("Repetições totais", "NUMBER", "repetições", NUMERIC_FUNCTIONS),
    AnalyticsField.PARTIAL_REPS: FieldDefinition("Repetições parciais", "NUMBER", "repetições", NUMERIC_FUNCTIONS),
    AnalyticsField.PARTIAL_REPS_RATIO: FieldDefinition("Repetições parciais / total", "NUMBER", "%", NUMERIC_FUNCTIONS),
    AnalyticsField.NON_PARTIAL_REPS: FieldDefinition("Repetições totais - parciais", "NUMBER", "repetições", NUMERIC_FUNCTIONS),
    AnalyticsField.EXECUTION: FieldDefinition("Tempo de execução", "NUMBER", "s", NUMERIC_FUNCTIONS),
    AnalyticsField.REST: FieldDefinition("Tempo de descanso", "NUMBER", "s", NUMERIC_FUNCTIONS),
    AnalyticsField.TECHNIQUE: FieldDefinition("Técnica", "CATEGORY", "", CATEGORY_FUNCTIONS, True),
    AnalyticsField.DATE: FieldDefinition("Data", "CATEGORY", "", CATEGORY_FUNCTIONS, True),
}

FUNCTION_LABELS = {
    Aggregation.RAW: "Valor original",
    Aggregation.COUNT: "Contagem",
    Aggregation.SUM: "Soma",
    Aggregation.AVG: "Média",
    Aggregation.MIN: "Mínimo",
    Aggregation.MAX: "Máximo",
}
