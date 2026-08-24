from django.db.models import Avg, Count, DateTimeField, F, Min
from django.db.models.functions import Coalesce

from .models import TrainingRecord


HISTORY_PAGE_SIZE = 20


def training_history_queryset(user, query=""):
    queryset = (
        TrainingRecord.objects
        .filter(user=user)
        .select_related("exercise")
        .prefetch_related("sets__advanced_technique")
        .annotate(
            set_total=Count("sets"),
            avg_weight=Avg("sets__weight_kg"),
            performed_at_sort=Coalesce(
                Min("sets__performed_at"),
                F("created_at"),
                output_field=DateTimeField(),
            ),
        )
        .order_by("-performed_at_sort", "-pk")
    )
    if query:
        queryset = queryset.filter(exercise__name__icontains=query)
    return queryset
