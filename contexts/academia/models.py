# Imports necessários para o Django descobrir os modelos organizados por feature.
from .features.catalog.models import AdvancedTechnique, Exercise
from .features.training.models import TrainingRecord, TrainingSet

__all__ = ["Exercise", "AdvancedTechnique", "TrainingRecord", "TrainingSet"]
