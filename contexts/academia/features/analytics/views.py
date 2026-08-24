import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, Paginator
from django.db.models import Avg, Count, DateTimeField, F, Min, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from contexts.academia.features.training.models import TrainingRecord, TrainingSet


HISTORY_PAGE_SIZE = 20


def _training_history_queryset(user):
    return (
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


@login_required
def dashboard(request):
    today = timezone.localdate()
    records = _training_history_queryset(request.user)
    history_page = Paginator(records, HISTORY_PAGE_SIZE).get_page(1)
    today_totals = TrainingSet.objects.filter(
        training_record__user=request.user,
        performed_at__date=today,
    ).aggregate(
        sets=Count("id"),
        execution=Sum("execution_time_seconds"),
        rest=Sum("rest_time_seconds"),
    )
    total_records = records.count()

    return render(request, "academia/dashboard.html", {
        "analysis_config": json.dumps({
            "endpoint": reverse("analytics_graphql:endpoint"),
            "startDate": today.replace(day=1).isoformat(),
            "endDate": today.isoformat(),
        }),
        "history_page": history_page,
        "today_totals": today_totals,
        "total_records": total_records,
    })


@login_required
def training_history(request):
    paginator = Paginator(_training_history_queryset(request.user), HISTORY_PAGE_SIZE)
    try:
        page_number = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        return JsonResponse({"detail": "Página inválida."}, status=400)

    if page_number < 1:
        return JsonResponse({"detail": "Página inválida."}, status=400)

    try:
        page = paginator.page(page_number)
    except EmptyPage:
        return JsonResponse({"html": "", "has_next": False, "next_page": None})

    return JsonResponse({
        "html": render_to_string(
            "academia/_training_history_rows.html",
            {"records": page.object_list},
            request=request,
        ),
        "has_next": page.has_next(),
        "next_page": page.next_page_number() if page.has_next() else None,
    })
