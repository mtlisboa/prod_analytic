from django.utils import timezone

from .forms import TrainingRecordForm, TrainingSetCreateFormSet
from .models import TrainingRecord


def build_create_training_forms(user, data=None):
    record = TrainingRecord(user=user)
    form = TrainingRecordForm(data, instance=record, user=user)
    initial = [{
        "position": 1,
        "performed_at": timezone.localtime().strftime("%Y-%m-%dT%H:%M"),
        "reps": 0,
        "partial_reps": 0,
        "execution_time_seconds": 1,
        "rest_time_seconds": 60,
    }]
    formset = TrainingSetCreateFormSet(
        data,
        instance=record,
        prefix="sets",
        form_kwargs={"user": user},
        initial=initial if data is None else None,
    )
    return record, form, formset
