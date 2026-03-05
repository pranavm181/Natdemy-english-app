from .models import ListeningLesson, ListeningQuestion

class ListeningQuestionInline(admin.TabularInline):
    model = ListeningQuestion
    extra = 3

@admin.register(ListeningLesson)
class ListeningLessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'xp_reward')
    list_filter = ('level',)
    inlines = [ListeningQuestionInline]
