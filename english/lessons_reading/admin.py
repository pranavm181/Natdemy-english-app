from django.contrib import admin
from .models import ReadingStory

@admin.register(ReadingStory)
class ReadingStoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'level')
    list_filter = ('level',)
    
    fieldsets = (
        ('Story Details', {
            'fields': ('title', 'level', 'story_content', 'background_image_url')
        }),
        ('Question 1', {
            'fields': ('q1_text', 'q1_option_1', 'q1_option_2', 'q1_option_3', 'q1_correct'),
            'description': 'Enter three options and mark the correct one.'
        }),
        ('Question 2', {
            'fields': ('q2_text', 'q2_option_1', 'q2_option_2', 'q2_option_3', 'q2_correct'),
            'description': 'Enter three options and mark the correct one.'
        }),
        ('Question 3', {
            'fields': ('q3_text', 'q3_option_1', 'q3_option_2', 'q3_option_3', 'q3_correct'),
            'description': 'Enter three options and mark the correct one.'
        }),
    )
