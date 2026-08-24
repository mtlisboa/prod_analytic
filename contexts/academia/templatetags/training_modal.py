from django import template

from contexts.academia.features.training.modal import build_create_training_forms


register = template.Library()


@register.inclusion_tag("academia/_training_create_modal.html", takes_context=True)
def training_registration_modal(context):
    request = context["request"]
    match = getattr(request, "resolver_match", None)
    if (
        not request.user.is_authenticated
        or not match
        or match.namespace != "academia"
        or match.url_name in {"training_create", "training_update"}
        or not request.user.exercises.exists()
    ):
        return {"enabled": False}

    _record, form, formset = build_create_training_forms(request.user)
    return {"enabled": True, "form": form, "formset": formset}
