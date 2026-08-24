import json
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone

from contexts.academia.features.training.models import TrainingSet
from contexts.academia.features.training.queries import training_history_queryset


@login_required
def dashboard(request):
    today = timezone.localdate()
    records = training_history_queryset(request.user)
    recent_records = records.filter(
        performed_at_sort__gte=timezone.now() - timedelta(days=5)
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
        "recent_records": recent_records,
        "today_totals": today_totals,
        "total_records": total_records,
    })
