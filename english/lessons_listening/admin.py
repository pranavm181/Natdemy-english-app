from django.contrib import admin
from .models import ListeningLesson

@admin.register(ListeningLesson)
class ListeningLessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'level')
    list_filter = ('level',)
    
    fieldsets = (
        ('Lesson Details', {
            'fields': ('title', 'youtube_url', 'level')
        }),
        ('Question 1', {
            'fields': ('q1_text', 'q1_option_1', 'q1_option_2', 'q1_option_3', 'q1_correct'),
        }),
        ('Question 2', {
            'fields': ('q2_text', 'q2_option_1', 'q2_option_2', 'q2_option_3', 'q2_correct'),
        }),
        ('Question 3 (Optional)', {
            'fields': ('q3_text', 'q3_option_1', 'q3_option_2', 'q3_option_3', 'q3_correct'),
        }),
    )
