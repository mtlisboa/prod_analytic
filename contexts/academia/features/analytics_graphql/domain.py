from dataclasses import dataclass
from enum import Enum

import strawberry


@strawberry.enum
class AnalyticsField(Enum):
    EXERCISE = "exercise"
    SET_POSITION = "set_position"
    WEIGHT = "weight"
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
