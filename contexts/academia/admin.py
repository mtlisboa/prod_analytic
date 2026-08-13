from django.contrib import admin

from .models import AdvancedTechnique, Exercise, TrainingRecord, TrainingSet

admin.site.register(Exercise)
admin.site.register(AdvancedTechnique)
admin.site.register(TrainingRecord)
admin.site.register(TrainingSet)
