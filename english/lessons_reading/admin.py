from django.contrib import admin
from .models import ReadingStory, ReadingQuestion

class ReadingQuestionInline(admin.TabularInline):
    model = ReadingQuestion
    extra = 3

@admin.register(ReadingStory)
class ReadingStoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'xp_reward')
    list_filter = ('level',)
    inlines = [ReadingQuestionInline]
