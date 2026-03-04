from django.contrib import admin
from .models import WritingTask

@admin.register(WritingTask)
class WritingTaskAdmin(admin.ModelAdmin):
    list_display = ('malayalam_meaning', 'level')
    list_filter = ('level',)
