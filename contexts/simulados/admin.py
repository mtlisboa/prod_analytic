from django.contrib import admin

from .models import Intervalo, Meta, MetaMateria, Simulado


class IntervaloInline(admin.TabularInline):
    model = Intervalo
    extra = 0


@admin.register(Simulado)
class SimuladoAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "exam_date", "correct_answers", "wrong_answers", "total_time_minutes")
    list_filter = ("exam_date",)
    search_fields = ("title", "user__username")
    inlines = (IntervaloInline,)


class MetaMateriaInline(admin.TabularInline):
    model = MetaMateria
    extra = 0


@admin.register(Meta)
class MetaAdmin(admin.ModelAdmin):
    list_display = ("exam_name", "user", "exam_date", "exam_time_minutes", "break_time_minutes")
    search_fields = ("exam_name", "user__username")
    inlines = (MetaMateriaInline,)
