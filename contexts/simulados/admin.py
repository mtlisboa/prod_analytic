from django.contrib import admin

from .models import Intervalo, Simulado


class IntervaloInline(admin.TabularInline):
    model = Intervalo
    extra = 0


@admin.register(Simulado)
class SimuladoAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "exam_date", "correct_answers", "wrong_answers", "total_time_minutes")
    list_filter = ("exam_date",)
    search_fields = ("title", "user__username")
    inlines = (IntervaloInline,)
