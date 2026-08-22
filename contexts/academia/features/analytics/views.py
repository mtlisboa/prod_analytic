import json

from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from contexts.academia.features.training.models import TrainingRecord, TrainingSet


@login_required
def dashboard(request):
    today = timezone.localdate()
    records = (
        TrainingRecord.objects
        .filter(user=request.user)
        .select_related("exercise")
        .prefetch_related("sets__advanced_technique")
        .annotate(set_total=Count("sets"), avg_weight=Avg("sets__weight_kg"))
        .order_by("-created_at")
    )
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
        "recent_records": records,
        "today_totals": today_totals,
        "total_records": total_records,
    })
